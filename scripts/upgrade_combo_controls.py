# SPDX-License-Identifier: GPL-3.0-or-later
"""Expose mounted light aiming beside stand height, with viewport dials."""
import bpy
import sys


def path(obj, name):
    m = next(m for m in obj.modifiers if m.type == 'NODES')
    s = next(s for s in m.node_group.interface.items_tree
             if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == name)
    return m.path_from_id() + '.properties.inputs.' + s.identifier + '.value'


def drive(owner, data_path, stand, name, index=None, radians=True):
    args = (data_path,) if index is None else (data_path, index)
    owner.driver_remove(*args)
    d = owner.driver_add(*args).driver
    d.expression = 'v*pi/180' if radians else 'v'
    v = d.variables.new(); v.name = 'v'; v.type = 'SINGLE_PROP'
    v.targets[0].id = stand; v.targets[0].data_path = path(stand, name)


def upgrade():
    for stand in list(bpy.data.objects):
        if stand.library or 'Kit | Combo Stand' not in stand.name:
            continue
        mount = next((o for o in stand.children if 'Receiver Mount' in o.name), None)
        if not mount:
            continue
        panel = stand.name.startswith('Panel')
        body = next(o for o in stand.children_recursive if o.type == 'MESH' and
                    any(m.type == 'NODES' for m in o.modifiers))
        m = next(m for m in stand.modifiers if m.type == 'NODES')
        if not m.node_group.get('sympatico_kit_controls'):
            g = m.node_group.copy(); m.node_group = g
            g.name = ('Panel' if panel else 'COB') + ' Kit | Stand and aiming controls'
            inp = next(n for n in g.nodes if n.bl_idname == 'NodeGroupInput')
            join = g.nodes['Stand and height handle']
            for label, axis, radius in [('Light Pan (deg)', (0,0,1), .25)]:
                s = g.interface.new_socket(name=label, in_out='INPUT', socket_type='NodeSocketFloat')
                s.min_value = -180; s.max_value = 180
                g.interface_update(bpy.context)
                value = stand.get(label, body.path_resolve(path(body, 'Tilt (deg)')) if panel and 'Tilt' in label else 0.)
                getattr(m.properties.inputs, s.identifier).value = value
                rad = g.nodes.new('ShaderNodeMath'); rad.operation = 'MULTIPLY'; rad.inputs[1].default_value = 0.017453292519943295; rad.name = label + ' radians'
                g.links.new(inp.outputs[label], rad.inputs[0])
                dial = g.nodes.new('GeometryNodeGizmoDial'); dial.name = label + ' handle'
                dial.inputs['Screen Space'].default_value = False
                dial.inputs['Up'].default_value = axis
                dial.inputs['Radius'].default_value = radius
                g.links.new(rad.outputs[0], dial.inputs['Value'])
                g.links.new(g.nodes['Height arrow over shaft'].outputs[0], dial.inputs['Position'])
                g.links.new(dial.outputs[0], join.inputs['Geometry'])
                rad.location = (-500, -700 if 'Pan' in label else -1000)
                dial.location = (-200, rad.location.y)
            g['sympatico_kit_controls'] = True
        m.name = 'Combo Kit — Height and Aiming'
        drive(mount, 'rotation_euler', stand, 'Light Pan (deg)', 2)
        for label in ['Light Pan (deg)', 'Light Tilt (deg)']:
            if label in stand:
                del stand[label]
        # The modifier rename changes existing driver paths targeting stand height.
        for obj in stand.children_recursive:
            if obj.animation_data:
                for fc in obj.animation_data.drivers:
                    for v in fc.driver.variables:
                        for t in v.targets:
                            if t.id == stand:
                                t.data_path = t.data_path.replace('modifiers["Combo Stand — Controls"]', 'modifiers["Combo Kit — Height and Aiming"]')
        stand.update_tag()
        print('UPGRADED', stand.name)
    for c in bpy.data.collections:
        if not c.library and c.name.startswith('Combo Stand +') and c.asset_data:
            c.asset_data.use_preferred_import_method = True
            c.asset_data.preferred_import_method = 'APPEND'
            c.asset_data.description = 'Editable stand and native light. Imports with Append. Select stand for Height, Bag It and Light Pan, including viewport handles. Select fixture for Tilt and lighting controls.'
    bpy.context.view_layer.update()


if __name__ == '__main__':
    upgrade()
    if '--save' in sys.argv:
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, compress=True)
