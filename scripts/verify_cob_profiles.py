# SPDX-License-Identifier: GPL-3.0-or-later
"""Render-test the open library after installing optional STORM IES files.
Run: blender -b library/Sympatico_Lighting_Native.blend --python scripts/verify_cob_profiles.py
Never saves the input blend. Results go to a new temporary directory.
"""
import tempfile
from pathlib import Path
OUTPUT=Path(tempfile.mkdtemp(prefix="cob-ies-test-"))
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector
def verify_profile_geometry():
    o=bpy.data.objects["COB Light"];m=o.modifiers[0]
    s=next(s for s in m.node_group.interface.items_tree if s.name=="Light Profile")
    p=getattr(m.properties.inputs,s.identifier)
    saved=(p.value,m.properties.inputs.Socket_10.value,m.properties.inputs.Socket_12.value)
    def snapshot():
     o.update_tag();bpy.context.view_layer.update()
     dg=bpy.context.evaluated_depsgraph_get();e=o.evaluated_get(dg);me=e.to_mesh()
     sig=(len(me.vertices),len(me.polygons),tuple(sorted(mat.name for mat in me.materials if mat)),
          tuple(round(v,5) for vert in me.vertices for v in vert.co))
     e.to_mesh_clear()
     return sig
    p.value="Default"
    baseline={}
    for mode in ["Bare","Reflector","Fresnel","Octobox"]:
     m.properties.inputs.Socket_10.value=mode
     if mode=="Fresnel":
      for a in [15,45]:
       m.properties.inputs.Socket_12.value=a;baseline[(mode,a)]=snapshot()
     else:baseline[mode]=snapshot()
    for label in [i.identifier for i in p.bl_rna.properties["value"].enum_items if i.identifier!="Default"]:
     p.value=label
     expected="Bare" if "Bare Head" in label else "Reflector" if "CPC" in label else ("Fresnel",15 if "Spot" in label else 45)
     for mode in ["Bare","Reflector","Fresnel","Octobox"]:
      m.properties.inputs.Socket_10.value=mode
      for angle in [17,38]:
       m.properties.inputs.Socket_12.value=angle
       assert snapshot()==baseline[expected],(label,mode,angle,"geometry mismatch")
       ies=next(x for x in o.children_recursive if x.get("sympatico_cob_ies"))
       if mode=="Bare" and angle==17:location=ies.location.z
       assert abs(ies.location.z-location)<1e-6
     assert m.properties.inputs.Socket_10.value=="Octobox"
     print("MATCH",label,expected,flush=True)
    p.value="Default"
    assert snapshot()==baseline["Octobox"],"Default did not restore saved manual selection"
    print("PASS: 48 profile/manual combinations; matching geometry and stable IES source; manual settings restored")
    
    p.value,m.properties.inputs.Socket_10.value,m.properties.inputs.Socket_12.value=saved
    o.update_tag();bpy.context.view_layer.update()

verify_profile_geometry()

o=bpy.data.objects["COB Light"];mod=o.modifiers[0]
socket=next(s for s in mod.node_group.interface.items_tree if s.name=="Light Profile")
profile=getattr(mod.properties.inputs,socket.identifier)
labels=[i.identifier for i in profile.bl_rna.properties["value"].enum_items]
for obj in bpy.data.objects:obj.hide_render=True
o.location=(0,0,0);o.rotation_euler=(0,0,0)
for obj in o.children_recursive:
 if obj.type=="LIGHT":obj.hide_render=False
mod.properties.inputs.Socket_10.value="Bare"
s=bpy.context.scene;s.render.engine="CYCLES";s.cycles.device="CPU";s.cycles.samples=32;s.cycles.use_denoising=False
s.render.resolution_x=128;s.render.resolution_y=128;s.render.resolution_percentage=100;s.render.use_compositing=False
s.world=bpy.data.worlds.new("Test black");s.world.use_nodes=True;s.world.node_tree.nodes["Background"].inputs["Strength"].default_value=0
bpy.ops.mesh.primitive_plane_add(size=20,location=(0,0,3),rotation=(math.pi,0,0))
mat=bpy.data.materials.new("Test white");mat.use_nodes=True
nt=mat.node_tree;nt.nodes.clear();bsdf=nt.nodes.new("ShaderNodeBsdfDiffuse");bsdf.inputs["Color"].default_value=(.8,.8,.8,1)
out=nt.nodes.new("ShaderNodeOutputMaterial");nt.links.new(bsdf.outputs[0],out.inputs[0]);bpy.context.object.data.materials.append(mat)
bpy.ops.object.camera_add(location=(0,0,.1))
cam=bpy.context.object;cam.rotation_euler=(0,math.pi,0);cam.data.type="ORTHO";cam.data.ortho_scale=10;s.camera=cam
if '--tilted' in sys.argv:
 from mathutils import Matrix
 tilt=next(x for x in mod.node_group.interface.items_tree if x.name=='Tilt (deg)')
 getattr(mod.properties.inputs,tilt.identifier).value=35
 o.update_tag();bpy.context.view_layer.update()
 rotation=Matrix.Rotation(math.pi/2,4,'Y')
 turn=Matrix.Translation((0,0,-.113)) @ Matrix.Rotation(math.radians(35),4,'X') @ Matrix.Translation((0,0,.113))
 for target in [cam,next(x for x in s.objects if x.type=='MESH' and x.name.startswith('Plane'))]:
  target.matrix_world=rotation @ turn @ target.matrix_world
 o.matrix_world=rotation @ o.matrix_world
results={}
for label in labels:
 profile.value=label;o.update_tag();bpy.context.view_layer.update()
 dg=bpy.context.evaluated_depsgraph_get()
 lights=[(x.name,x.evaluated_get(dg).data.energy) for x in o.children_recursive if x.type=="LIGHT"]
 assert sum(power>0 for _,power in lights)==1,(label,lights)
 for x in o.children_recursive:
  if x.type!="LIGHT":continue
  for owner in (x,x.data,x.data.node_tree):
   if owner and owner.animation_data:
    assert all(d.driver.is_valid for d in owner.animation_data.drivers),(label,x.name)
 s.render.image_settings.file_format="OPEN_EXR";s.render.filepath=str(OUTPUT/(str(len(results))+".exr"))
 bpy.ops.render.render(write_still=True)
 im=bpy.data.images.load(s.render.filepath,check_existing=False);pixels=list(im.pixels)
 weights=[sum(pixels[i:i+3])/3 for i in range(0,len(pixels),4)]
 total=sum(weights)
 assert total>0.1,(label,"black output")
 radius=sum(w*((i%128-63.5)**2+(i//128-63.5)**2) for i,w in enumerate(weights))/total
 results[label]={"mean":total/len(weights),"peak":max(weights),"radius":math.sqrt(radius),"lights":lights}
 print("PROFILE_RESULT",label,results[label],flush=True)
 bpy.data.images.remove(im)
assert results[labels[2]]["radius"]<results[labels[3]]["radius"]<results[labels[4]]["radius"]
assert results[labels[5]]["radius"]<results[labels[6]]["radius"]
(OUTPUT/"results.json").write_text(json.dumps(results,indent=2))
print("PASS profiles: nonzero renders, correct active source, valid drivers, expected beam widths")

print("Results:",OUTPUT)
