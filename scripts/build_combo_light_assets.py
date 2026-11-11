# SPDX-License-Identifier: GPL-3.0-or-later
"""Build Combo Stand + COB / Panel collection assets in the open library.
Run with Blender --python this_script -- --save to save the current library.
"""
import math
import sys
import bpy
from mathutils import Matrix

CATALOG = "f276180a-73ac-5940-88bb-33fe5701c1a7"


def socket_path(obj, name):
    mod = next(m for m in obj.modifiers if m.type == 'NODES')
    sock = next(s for s in mod.node_group.interface.items_tree
                if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == name)
    return mod.path_from_id() + '.properties.inputs.' + sock.identifier + '.value'


def driver(owner, path, index, expression, targets):
    fc = owner.driver_add(path, index)
    d = fc.driver
    d.type = 'SCRIPTED'
    d.expression = expression
    for name, (obj, data_path) in targets.items():
        v = d.variables.new()
        v.name = name
        v.type = 'SINGLE_PROP'
        v.targets[0].id = obj
        v.targets[0].data_path = data_path


def clone_fixture(source, collection, prefix):
    mapping = {}
    for old in source.objects:
        obj = old.copy()
        obj.name = prefix + old.name
        if old.data:
            obj.data = old.data.copy()
        if obj.asset_data:
            obj.asset_clear()
        collection.objects.link(obj)
        mapping[old] = obj
    for old, obj in mapping.items():
        if old.parent in mapping:
            obj.parent = mapping[old.parent]
        for constraint in obj.constraints:
            if hasattr(constraint, "target") and constraint.target in mapping:
                constraint.target = mapping[constraint.target]
        for owner in (obj, obj.data, getattr(obj.data, 'node_tree', None)):
            if owner and owner.animation_data:
                for fc in owner.animation_data.drivers:
                    for var in fc.driver.variables:
                        for target in var.targets:
                            if target.id in mapping:
                                target.id = mapping[target.id]
    return mapping


def empty(name, collection, parent):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.parent = parent
    obj.empty_display_type = 'PLAIN_AXES'
    obj.empty_display_size = .08
    return obj


def part(name, collection, parent, location, scale, cylinder=False, rotation=(0, 0, 0)):
    if cylinder:
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=1, depth=2)
    else:
        bpy.ops.mesh.primitive_cube_add(size=2)
    obj = bpy.context.object
    obj.name = name
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)
    obj.parent = parent
    obj.location = location
    obj.scale = scale
    obj.rotation_euler = rotation
    mat = bpy.data.materials.get('Yoke | Graphite metal')
    if mat:
        obj.data.materials.append(mat)
    return obj


def build():
    for kind, source_name, body_name, x in [
        ('COB', 'COB Light — Native Fresnel', 'COB Light', 8.0),
        ('Panel', 'Panel Light — Native Area', 'Panel Light', 11.0),
    ]:
        name = 'Combo Stand + ' + kind + ' Light'
        if bpy.data.collections.get(name):
            raise RuntimeError(f'{name} already exists; refusing to overwrite an edited kit')
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        collection.instance_offset = (x, 0, 0)
        stand = bpy.data.objects['Combo Stand'].copy()
        stand.data = stand.data.copy()
        stand.name = kind + ' Kit | Combo Stand'
        stand.asset_clear()
        collection.objects.link(stand)
        stand.location = (x, 0, 0)
        stand.rotation_euler = (0, 0, 0)
        stand.scale = (1, 1, 1)
        stand['Light Pan (deg)'] = 0.0
        stand.id_properties_ui('Light Pan (deg)').update(
            description="Rotate the mounted light around the receiver without rotating the legs",
            min=-360, max=360)
        mount = empty(kind + ' Kit | Receiver Mount', collection, stand)
        # Match the stand node tree's physical extension clamp.
        driver(mount, 'location', 2, 'min(max(h,54.2),177.5)*.0254',
               {'h': (stand, socket_path(stand, 'Stand Height (in)'))})
        driver(mount, 'rotation_euler', 2, 'p*pi/180',
               {'p': (stand, '["Light Pan (deg)"]')})
        mapping = clone_fixture(bpy.data.collections[source_name], collection, kind + ' Kit | ')
        body = mapping[bpy.data.objects[body_name]]
        body.matrix_parent_inverse = Matrix.Identity(4)
        body.scale = (1, 1, 1)
        body.rotation_euler = (math.pi / 2, 0, 0)

        if kind == 'Panel':
            body.parent = mount
            body.location = (0, 0, 0)
            # The shoulder sits 19 mm below the yoke-clearance radius.
            driver(body, 'location', 2,
                   'sqrt((h*.1524)**2+(d*.1524+max(e*.0254*r,g*.0254*c))**2)+.059',
                   {k: (body, socket_path(body, label)) for k, label in [
                       ('h', 'Height (ft)'), ('d', 'Depth (ft)'),
                       ('e', 'Edge Depth (in)'), ('r', 'Front Rim'),
                       ('g', 'Grid Depth (in)'), ('c', 'Egg Crate')]})
        else:
            body.parent = mount
            body.location = (0, -.113, .30)
        collection.asset_mark()
        collection.asset_data.catalog_id = CATALOG
        collection.asset_data.author = 'Sympatico'
        collection.asset_data.description = (
            f'Combo Stand with native {kind} light. Select stand for height/sandbag and '
            'Custom Properties for light pan' + ('/tilt. ' if kind == 'COB' else '. ') +
            'Select fixture for lighting controls. Move the stand to move the complete kit.')
        collection.asset_generate_preview()
        print('BUILT', name, 'objects', len(collection.objects))
    import runpy
    from pathlib import Path
    runpy.run_path(str(Path(__file__).with_name('upgrade_combo_controls.py')))['upgrade']()
    bpy.context.view_layer.update()


if __name__ == '__main__':
    build()
    if '--save' in sys.argv:
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, compress=True)
