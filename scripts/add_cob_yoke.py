# SPDX-License-Identifier: GPL-3.0-or-later
"""Add fixture-owned COB yoke and panel-style Tilt controls. --save saves library."""
import bpy, math, sys
from mathutils import Matrix
from pathlib import Path
import runpy
helpers = runpy.run_path(str(Path(__file__).with_name('upgrade_combo_controls.py')))
path, drive = helpers['path'], helpers['drive']


def geometry(g):
    if g.nodes.get('COB yoke and tilted head'):
        return
    inp = next(n for n in g.nodes if n.type == 'GROUP_INPUT')
    out = next(n for n in g.nodes if n.type == 'GROUP_OUTPUT')
    source = out.inputs['Geometry'].links[0].from_socket
    y = g.interface.new_socket(name='Yoke', in_out='INPUT', socket_type='NodeSocketBool'); y.default_value=True
    t = g.interface.new_socket(name='Tilt (deg)', in_out='INPUT', socket_type='NodeSocketFloat')
    t.min_value=-180; t.max_value=180
    g.interface_update(bpy.context)
    def node(kind,name):
        n=g.nodes.new(kind);n.name=name;return n
    def transform(src,translation=(0,0,0),rotation=(0,0,0)):
        n=node('GeometryNodeTransform','COB yoke placement')
        n.inputs['Translation'].default_value=translation;n.inputs['Rotation'].default_value=rotation
        g.links.new(src,n.inputs['Geometry']);return n
    rad=node('ShaderNodeMath','COB tilt radians');rad.operation='MULTIPLY';rad.inputs[1].default_value=math.pi/180
    g.links.new(inp.outputs['Tilt (deg)'],rad.inputs[0])
    xyz=node('ShaderNodeCombineXYZ','COB tilt rotation');g.links.new(rad.outputs[0],xyz.inputs['X'])
    before=transform(source,(0,0,.113))
    turn=transform(before.outputs[0]);g.links.new(xyz.outputs[0],turn.inputs['Rotation'])
    after=transform(turn.outputs[0],(0,0,-.113))
    yoke=node('GeometryNodeJoinGeometry','COB fixed yoke')
    def piece(center,size,cylinder=False,rotation=(0,0,0)):
        n=node('GeometryNodeMeshCylinder' if cylinder else 'GeometryNodeMeshCube','COB yoke part')
        if cylinder:
            n.inputs['Vertices'].default_value=32;n.inputs['Radius'].default_value=size[0];n.inputs['Depth'].default_value=size[2]
        else:n.inputs['Size'].default_value=size
        p=transform(n.outputs['Mesh'],center,rotation)
        g.links.new(p.outputs[0],yoke.inputs['Geometry'])
    piece((0,-.35,-.113),(.01425,0,.1),True,(math.pi/2,0,0))
    piece((0,-.294,-.113),(.023,0,.012),True,(math.pi/2,0,0))
    piece((0,-.276,-.113),(.24,.024,.036))
    for sign in [-1,1]:
        piece((sign*.108,-.138,-.113),(.024,.30,.036))
        piece((sign*.132,0,-.113),(.026,0,.028),True,(0,math.pi/2,0))
    mat=node('GeometryNodeSetMaterial','COB yoke graphite')
    mat.inputs['Material'].default_value=bpy.data.materials.get('Yoke | Graphite metal')
    g.links.new(yoke.outputs[0],mat.inputs['Geometry'])
    switch=node('GeometryNodeSwitch','COB yoke visibility');switch.input_type='GEOMETRY'
    g.links.new(inp.outputs['Yoke'],switch.inputs['Switch']);g.links.new(mat.outputs[0],switch.inputs['True'])
    dial=node('GeometryNodeGizmoDial','COB tilt dial')
    dial.inputs['Screen Space'].default_value=False
    dial.inputs['Position'].default_value=(.15,0,-.113);dial.inputs['Up'].default_value=(1,0,0);dial.inputs['Radius'].default_value=.18
    g.links.new(rad.outputs[0],dial.inputs['Value'])
    join=node('GeometryNodeJoinGeometry','COB yoke and tilted head')
    for output in [after.outputs[0],switch.outputs[0],dial.outputs[0]]:g.links.new(output,join.inputs['Geometry'])
    g.links.new(join.outputs[0],out.inputs['Geometry'])
    # Keep the new assembly readable in the node editor.
    new=[n for n in g.nodes if n.name.startswith('COB ')];frame=node('NodeFrame','COB | Yoke and physical tilt')
    for i,n in enumerate(new):n.parent=frame;n.location=(i%5*220,-(i//5)*230)
    frame.location=(0,-1800)


def upgrade():
    bodies=[o for o in bpy.data.objects if not o.library and any(m.type=='NODES' and m.name=='COB — Controls' for m in o.modifiers)]
    for body in bodies:
        mod=next(m for m in body.modifiers if m.name=='COB — Controls')
        geometry(mod.node_group)
        if not body.get('sympatico_cob_yoke'):
            sock=next(s for s in mod.node_group.interface.items_tree if s.name=='Yoke')
            getattr(mod.properties.inputs,sock.identifier).value=True
            body['sympatico_cob_yoke']=True
        pivot=next((o for o in body.children if o.get('sympatico_cob_tilt')),None)
        if pivot is None:
            pivot=bpy.data.objects.new(body.name+' | Physical tilt pivot',None)
            for c in body.users_collection:c.objects.link(pivot)
            pivot.parent=body;pivot.location=(0,0,-.113);pivot.empty_display_size=.05
            pivot['sympatico_cob_tilt']=True
            for light in list(body.children):
                if light.type=='LIGHT':
                    light.parent=pivot
                    light.matrix_parent_inverse=Matrix.Translation((0,0,.113))
        drive(pivot,'rotation_euler',body,'Tilt (deg)',0)
        # Replace the stand-owned yoke and outer tilt pivot in existing kits.
        old=body.parent
        if old and old.name.startswith('COB Kit | Tilt Pivot'):
            mount=old.parent
            body.parent=mount;body.matrix_parent_inverse=Matrix.Identity(4)
            body.location=(0,-.113,.30)
            body.rotation_euler=(math.pi/2,0,0)
            for obj in list(mount.children):
                if obj != body and (obj == old or any(label in obj.name for label in ['Junior Pin','Mount Shoulder','Yoke Crossbar','Yoke Arm','Tilt Handle'])):
                    bpy.data.objects.remove(obj,do_unlink=True)
        body.update_tag()
        print('COB YOKE',body.name)
    bpy.context.view_layer.update()


if __name__=='__main__':
    upgrade()
    if '--save' in sys.argv:bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
