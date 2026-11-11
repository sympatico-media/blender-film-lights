# SPDX-License-Identifier: GPL-3.0-or-later
"""Upgrade the open file's COB fixtures in memory; caller chooses where to save.
Run in Blender's Python console:
    import runpy; _ = runpy.run_path(SCRIPT_PATH, run_name="__main__")
No scene render settings are changed. Existing Fresnel object names are retained.
"""
import math
import json
from pathlib import Path
import bpy

def drive(owner, path, expression, controls, variables, index=None):
    try:
        if index is None:
            owner.driver_remove(path)
        else:
            owner.driver_remove(path, index)
    except (TypeError, RuntimeError):
        pass
    curve = owner.driver_add(path) if index is None else owner.driver_add(path, index)
    driver = curve.driver
    driver.type = 'SCRIPTED'
    for var in list(driver.variables):
        driver.variables.remove(var)
    for name, target_path in variables.items():
        var = driver.variables.new()
        var.name = name
        var.type = 'SINGLE_PROP'
        var.targets[0].id = controls
        var.targets[0].data_path = target_path
    driver.expression = expression

def upgrade():
    updated = []
    for body in list(bpy.data.objects):
        mods = [m for m in body.modifiers if m.type == 'NODES' and m.node_group
                and m.name == 'COB — Controls']
        if not mods:
            continue
        mod = mods[0]
        sockets = {s.name: s.identifier for s in mod.node_group.interface.items_tree
                   if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}
        base = mod.path_from_id() + '.properties.inputs.'
        def prop(name):
            return base + sockets[name] + '.value'
        menu = getattr(mod.properties.inputs, sockets['Attachment'])
        ids = {i.identifier: i.value for i in menu.bl_rna.properties['value'].enum_items}
        fabric = getattr(mod.properties.inputs, sockets['Octobox Fabric'])
        fabrics = {i.identifier: i.value for i in fabric.bl_rna.properties['value'].enum_items}
        children = [o for o in body.children_recursive if o.type == 'LIGHT' and o.data.type == 'SPOT']
        if len(children) != 1:
            raise RuntimeError(f"{body.name}: expected one parented native Spot, got {len(children)}")
        spot = children[0]
        # Each fixture needs independent light data/driver targets.
        if spot.data.users > 1:
            spot.data = spot.data.copy()
        area = next((o for o in body.children_recursive if o.get('sympatico_cob_area')), None)
        if area is None:
            data = bpy.data.lights.new(body.name + ' | Native Area', 'AREA')
            area = bpy.data.objects.new(body.name + ' | Area source', data)
            for collection in body.users_collection:
                collection.objects.link(area)
            area.parent = body
            area.rotation_euler = (math.pi, 0, 0)
            area['sympatico_cob_area'] = True
            # Preserve the existing temperature/RGB color shader and its drivers.
            data.use_nodes = True
            nt = data.node_tree
            nt.nodes.clear()
            output = nt.nodes.new('ShaderNodeOutputLight')
            emission = nt.nodes.new('ShaderNodeEmission')
            temp = nt.nodes.new('ShaderNodeBlackbody')
            mix = nt.nodes.new('ShaderNodeMixRGB')
            mix.blend_type = 'MIX'
            nt.links.new(temp.outputs[0], mix.inputs[1])
            nt.links.new(mix.outputs[0], emission.inputs['Color'])
            nt.links.new(emission.outputs[0], output.inputs['Surface'])
            drive(nt, temp.inputs[0].path_from_id('default_value'), 'v', body, {'v': prop('Temperature (K)')})
            drive(nt, mix.inputs[0].path_from_id('default_value'), 'v', body, {'v': prop('RGB Mix')})
            for axis in range(3):
                drive(nt, mix.inputs[2].path_from_id('default_value'), 'v', body,
                      {'v': prop('RGB') + f'[{axis}]'}, axis)
        area.data.shape = 'DISK'
        area.data.normalize = True
        for obj in (spot, area):
            obj.data.cycles.max_bounces = 1024
            obj.data.diffuse_factor = 1
            obj.data.specular_factor = 1
            obj.data.transmission_factor = 1
            obj.data.volume_factor = 1
            obj.visible_diffuse = True
            obj.visible_glossy = True
            obj.visible_transmission = True
            obj.visible_volume_scatter = True
            for axis in range(3):
                drive(obj, 'scale', '1/max(abs(s),0.000001)', body,
                      {'s': f'scale[{axis}]'}, axis)
        variables = {'w': prop('Wattage'), 'mode': prop('Attachment'),
                     'a': prop('Fresnel Beam (deg)'), 'd': prop('Reflector Depth (in)'),
                     'r': prop('Reflector Diameter (in)'), 'c': prop('COB Diameter (in)')}
        # Keep the established Fresnel power mapping; Reflector is a native cone.
        drive(spot.data, 'energy',
              f'w*0.905*4*pi/(1-0.5*(cos(a*pi/360)**2+cos(a*pi/360*0.85)**2)) if mode=={ids["Fresnel"]} else (w*pi if mode=={ids["Reflector"]} else 0)',
              body, variables)
        drive(spot.data, 'spot_size',
              f'a*pi/180 if mode=={ids["Fresnel"]} else min(pi-0.001,max(0.05,2*atan(max(r,c)*0.5/max(d,0.01))))',
              body, variables)
        drive(spot.data, 'shadow_soft_size',
              f'r*.0254 if mode=={ids["Fresnel"]} else c*.0127',
              body, {'mode': prop('Attachment'), 'r': prop('Fresnel Source Radius (in)'), 'c': prop('COB Diameter (in)')})
        drive(spot, 'location',
              f'((.292-.0026*a+r*.0254) if mode=={ids["Fresnel"]} else (d*.0254+c*.0127+.003))/max(abs(s),0.000001)',
              body, {'mode': prop('Attachment'), 'a': prop('Fresnel Beam (deg)'),
                     'r': prop('Fresnel Source Radius (in)'), 'd': prop('Reflector Depth (in)'),
                     'c': prop('COB Diameter (in)'), 's': 'scale[2]'}, 2)
        # Sum of direct and scattered coefficients from the existing fitted fabrics.
        fit = Path(__file__).resolve().parents[1] / 'research/diffusion_calibration_2026-10-07/validation/fit_parameters.json'
        presets = json.loads(fit.read_text())['presets']
        gains = {}
        for label, material in [('Full Silk', 'Diffusion 2 | Silk'),
                                ('Half Silk', 'Diffusion 3 | Half Silk'),
                                ('Quarter Silk', 'Diffusion 4 | Quarter Silk')]:
            gains[label] = presets[material]['direct'] + presets[material]['scattered']
        transmission = (f'({gains["Full Silk"]} if f=={fabrics["Full Silk"]} else '
                        f'({gains["Half Silk"]} if f=={fabrics["Half Silk"]} else {gains["Quarter Silk"]}))')
        drive(area.data, 'energy',
              f'w*pi if mode=={ids["Bare"]} else (w*pi*{transmission} if mode=={ids["Octobox"]} else 0)',
              body, {'w': prop('Wattage'), 'mode': prop('Attachment'), 'f': prop('Octobox Fabric')})
        drive(area.data, 'size',
              f'max(c*.0254,0.0001) if mode=={ids["Bare"]} else max(z,c)*.0254*cos(pi/8)',
              body, {'mode': prop('Attachment'), 'c': prop('COB Diameter (in)'), 'z': prop('Octobox Size (in)')})
        drive(area, 'location',
              f'(0.001 if mode=={ids["Bare"]} else d*.0254+.006)/max(abs(s),0.000001)',
              body, {'mode': prop('Attachment'), 'd': prop('Octobox Depth (in)'), 's': 'scale[2]'}, 2)
        # Re-running the native upgrade must preserve an installed IES override.
        if 'Light Profile' in sockets:
            selected = getattr(mod.properties.inputs, sockets['Light Profile'])
            default = next(i.value for i in selected.bl_rna.properties['value'].enum_items
                           if i.identifier == 'Default')
            for native in (spot, area):
                curve = next(d for d in native.data.animation_data.drivers if d.data_path == 'energy')
                original = curve.driver.expression
                var = curve.driver.variables.new()
                var.name = 'lp'
                var.type = 'SINGLE_PROP'
                var.targets[0].id = body
                var.targets[0].data_path = prop('Light Profile')
                curve.driver.expression = f'({original}) if lp=={default} else 0'
        updated.append(body.name)

    # The COB disk remains visible, but cannot emit extra illumination.
    for mat in bpy.data.materials:
        if not mat.name.startswith('COB | One-sided emitter') or not mat.use_nodes:
            continue
        nt = mat.node_tree
        output = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
        if nt.nodes.get('Native COB | appearance only'):
            continue
        original = output.inputs['Surface'].links[0].from_socket
        path = nt.nodes.new('ShaderNodeLightPath')
        path.name = 'Native COB | appearance only'
        transparent = nt.nodes.new('ShaderNodeBsdfTransparent')
        mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(path.outputs['Is Camera Ray'], mix.inputs[0])
        nt.links.new(transparent.outputs[0], mix.inputs[1])
        nt.links.new(original, mix.inputs[2])
        nt.links.new(mix.outputs[0], output.inputs['Surface'])
        mat.cycles.emission_sampling = 'NONE'
    bpy.context.view_layer.update()
    print('UPGRADED_COB', updated)
    return updated

if __name__ == '__main__':
    upgrade()
