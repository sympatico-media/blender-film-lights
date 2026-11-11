# SPDX-License-Identifier: GPL-3.0-or-later
"""Make fixture and kit aiming dials usable like the C-Stand handles."""
import bpy
import sys


def upgrade():
    for group in bpy.data.node_groups:
        if group.library:
            continue
        for node in group.nodes:
            if node.bl_idname != 'GeometryNodeGizmoDial':
                continue
            if node.name not in {'COB tilt dial', 'Yoke tilt dial',
                                 'Light Pan (deg) handle', 'Light Tilt (deg) handle'}:
                continue
            # Match C-Stand's invertible degree conversion for gizmo editing.
            value_node = node.inputs['Value'].links[0].from_node
            if value_node.bl_idname == 'ShaderNodeMath' and value_node.operation == 'RADIANS':
                value_node.operation = 'MULTIPLY'
                value_node.inputs[1].default_value = 0.017453292519943295
            node.inputs['Screen Space'].default_value = False
            node.inputs['Radius'].default_value = .24 if node.name == 'Yoke tilt dial' else .18 if 'tilt' in node.name.lower() else .25
            if node.name == 'COB tilt dial':
                node.inputs['Position'].default_value = (.15, 0, -.113)
            print('YOKE HANDLE', group.name, node.name)
    # A driven Tilt input cannot be edited with a viewport gizmo. Make the
    # fixture the owner of tilt in kits too, so selecting the yoke always works.
    import runpy
    from pathlib import Path
    h = runpy.run_path(str(Path(__file__).with_name('upgrade_combo_controls.py')))
    for stand in list(bpy.data.objects):
        if stand.library or 'Kit | Combo Stand' not in stand.name:
            continue
        mount = next((o for o in stand.children if 'Receiver Mount' in o.name), None)
        if not mount:
            continue
        body = next(o for o in stand.children_recursive if o.type == 'MESH' and any(m.type == 'NODES' for m in o.modifiers))
        tilt_path = h['path'](body, 'Tilt (deg)')
        value = body.path_resolve(tilt_path)
        body.driver_remove(tilt_path)
        mod = next(m for m in body.modifiers if m.type == 'NODES')
        sock = next(s for s in mod.node_group.interface.items_tree if s.name == 'Tilt (deg)')
        getattr(mod.properties.inputs, sock.identifier).value = value
        pivot = next((o for o in body.children if o.get('sympatico_cob_tilt')), None)
        if pivot:
            h['drive'](pivot, 'rotation_euler', body, 'Tilt (deg)', 0)
        group = next(m for m in stand.modifiers if m.type == 'NODES').node_group
        for n in list(group.nodes):
            if n.name in {'Light Tilt (deg) handle', 'Light Tilt (deg) radians'}:
                group.nodes.remove(n)
        for item in list(group.interface.items_tree):
            if item.name == 'Light Tilt (deg)':
                group.interface.remove(item)
        body.update_tag()
    bpy.context.view_layer.update()


if __name__ == '__main__':
    upgrade()
    if '--save' in sys.argv:
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, compress=True)
