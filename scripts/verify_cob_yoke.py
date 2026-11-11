# SPDX-License-Identifier: GPL-3.0-or-later
"""Verify COB head geometry, native sources, fixed yoke and isolated imports."""
import bpy,math
from mathutils import Matrix,Vector
source=bpy.data.filepath
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(source,link=False) as (_,data):data.collections=['COB Light — Native Fresnel']
c=data.collections[0];bpy.context.scene.collection.children.link(c)
b=next(o for o in c.objects if any(m.name=='COB — Controls' for m in o.modifiers));m=b.modifiers[0]
ctrl={s.name:getattr(m.properties.inputs,s.identifier) for s in m.node_group.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT'}
def update():b.update_tag();bpy.context.view_layer.update();return bpy.context.evaluated_depsgraph_get()
def vertices():
 e=b.evaluated_get(update());mesh=e.to_mesh();v=[x.co.copy() for x in mesh.vertices];e.to_mesh_clear();return v
assert ctrl['Yoke'].value
ctrl['Yoke'].value=False
base=vertices()
lights=[o for o in b.children_recursive if o.type=='LIGHT']
base_matrices={o:o.matrix_world.copy() for o in lights}
for angle in [-60,35,90]:
 ctrl['Tilt (deg)'].value=angle
 verts=vertices()
 turn=Matrix.Translation((0,0,-.113)) @ Matrix.Rotation(math.radians(angle),4,'X') @ Matrix.Translation((0,0,.113))
 assert len(base)==len(verts)
 assert max((turn@a-z).length for a,z in zip(base,verts))<1e-5
 for o in lights:
  expected=b.matrix_world @ turn @ b.matrix_world.inverted() @ base_matrices[o]
  assert max(abs(o.matrix_world[i][j]-expected[i][j]) for i in range(4) for j in range(4))<1e-5,(angle,o.name)
ctrl['Tilt (deg)'].value=0;ctrl['Yoke'].value=True
with_yoke=vertices();extra=len(with_yoke)-len(base);assert extra>0
ctrl['Tilt (deg)'].value=60
turned=vertices()
# Join input ordering is stable; all fixed vertices must stay at their original positions.
fixed=sum((a-z).length<1e-6 for a,z in zip(with_yoke,turned))
assert fixed>=extra,(fixed,extra)
assert all(o.parent in set(c.objects) for o in lights)
print('PASS: fixture Tilt rotates geometry and all native sources together; Yoke toggle and fixed mounting geometry')
