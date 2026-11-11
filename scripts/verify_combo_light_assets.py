# SPDX-License-Identifier: GPL-3.0-or-later
"""Append each stand kit twice into a fresh scene and test mounting/isolation.
Run: blender -b library/Sympatico_Lighting_Native.blend --python scripts/verify_combo_light_assets.py
The input file is never saved.
"""
import math
import bpy

source = bpy.data.filepath
bpy.ops.wm.read_factory_settings(use_empty=True)

def controls(obj):
    m = next(m for m in obj.modifiers if m.type == 'NODES')
    return {s.name: getattr(m.properties.inputs, s.identifier)
            for s in m.node_group.interface.items_tree
            if s.item_type == 'SOCKET' and s.in_out == 'INPUT'}


def update(obj):
    obj.update_tag()
    bpy.context.view_layer.update()
    return bpy.context.evaluated_depsgraph_get()


def power(body):
    dg = update(body)
    return sum(o.evaluated_get(dg).data.energy for o in body.children_recursive if o.type == 'LIGHT')


for kind in ['COB', 'Panel']:
    kits = []
    for _ in range(2):
        with bpy.data.libraries.load(source, link=False) as (_, data):
            data.collections = ['Combo Stand + ' + kind + ' Light']
        coll = data.collections[0]
        bpy.context.scene.collection.children.link(coll)
        members = set(coll.objects)
        assert coll.asset_data
        assert coll.asset_data.use_preferred_import_method
        assert coll.asset_data.preferred_import_method == 'APPEND'
        for obj in coll.objects:
            assert obj.parent is None or obj.parent in members
            for owner in (obj, obj.data, getattr(obj.data, 'node_tree', None)):
                if owner and owner.animation_data:
                    for fc in owner.animation_data.drivers:
                        for var in fc.driver.variables:
                            for target in var.targets:
                                if isinstance(target.id, bpy.types.Object):
                                    assert target.id in members, (kind,obj.name,target.id.name)
        stand = next(o for o in coll.objects if 'Kit | Combo Stand' in o.name)
        body = next(o for o in coll.objects if o.type=='MESH'
                    and any(m.type=='NODES' and ('COB' in m.name if kind=='COB' else 'Procedural Light' in m.name)
                            for m in o.modifiers))
        mount = next(o for o in coll.objects if 'Receiver Mount' in o.name)
        kits.append((coll,stand,body,mount))
    first, second = kits
    coll, stand, body, mount = first
    baseline = power(second[2])
    c = controls(body)
    c['Wattage'].value = 123
    assert abs(power(second[2])-baseline)<1e-4, 'power leaked to second kit'
    for height in [54.2,83,120,177.5]:
        controls(stand)['Stand Height (in)'].value = height
        dg = update(stand)
        expected = height*.0254
        actual = (stand.matrix_world.inverted() @ mount.matrix_world).translation.z
        assert abs(expected-actual)<1e-5, (kind,height,actual)
        if kind=='Panel':
            for size in [2,4,6]:
                c['Height (ft)'].value=size
                c['Tilt (deg)'].value=35
                update(stand)
                dg=update(body)
                e=body.evaluated_get(dg);mesh=e.to_mesh()
                a=mesh.attributes['yoke_part']
                assert a.domain=='FACE'
                vertices={v for p in mesh.polygons if a.data[p.index].value==5 for v in p.vertices}
                assert vertices
                lowest=min((e.matrix_world @ mesh.vertices[v].co).z for v in vertices)
                assert abs(lowest-mount.matrix_world.translation.z)<1e-4, ('unseated panel shoulder',lowest)
                e.to_mesh_clear()
    if kind=='COB':
        c['Light Profile'].value='STORM 1200x — CPC 30°'
        dg=update(body)
        active=[o for o in body.children_recursive if o.type=='LIGHT' and o.evaluated_get(dg).data.energy>0]
        assert len(active)==1 and active[0].get('sympatico_cob_ies')
        assert controls(second[2])['Light Profile'].value=='Default'
    controls(stand)['Light Pan (deg)'].value=45
    if kind=='COB':
        c['Tilt (deg)'].value=30
    update(body)
    update(stand)
    assert abs(mount.rotation_euler.z-math.pi/4)<1e-6
    if kind == 'COB':
        pivot = next(o for o in body.children if o.get('sympatico_cob_tilt'))
        assert abs(pivot.rotation_euler.x-math.pi/6)<1e-6
    else:
        assert abs(c['Tilt (deg)'].value-35)<1e-6
    assert controls(second[1])['Light Pan (deg)'].value == 0
    group = next(m for m in stand.modifiers if m.type == 'NODES').node_group
    assert sum(n.bl_idname == 'GeometryNodeGizmoDial' for n in group.nodes) == 1
    for obj in coll.objects:
        for owner in (obj,obj.data,getattr(obj.data,'node_tree',None)):
            if owner and owner.animation_data:
                assert all(fc.driver.is_valid for fc in owner.animation_data.drivers),obj.name
    print('PASS',kind,': repeated append, internal drivers, height tracking, aiming, independent controls')
