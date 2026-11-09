# SPDX-License-Identifier: GPL-3.0-or-later
"""Run with Blender -b LIBRARY.blend --python scripts/verify_cob_native.py.
Builds a temporary scene in memory; never saves the input blend file.
"""
import tempfile
from pathlib import Path
output_dir=Path(tempfile.mkdtemp(prefix="cob-native-test-"))
import bpy, math, json
from mathutils import Vector
o=bpy.data.objects["COB Light"]
light=bpy.data.objects["COB Light | Fresnel Spot"]
area=next(x for x in o.children if x.type=="LIGHT" and x.data.type=="AREA")
for obj in bpy.data.objects:
    obj.hide_render=obj not in [o,light,area]
o.location=(0,0,1.2)
o.rotation_euler=(math.pi/2,0,0) # local +Z points -Y
o.rotation_euler=(-math.pi/2,0,0) # local +Z points +Y
o.scale=(1,1,1)
s=bpy.context.scene
s.render.engine="CYCLES"
s.cycles.device="CPU"
s.cycles.samples=32
s.cycles.use_denoising=False
s.render.resolution_x=128;s.render.resolution_y=128;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new("Test black world");s.world.use_nodes=True
s.world.node_tree.nodes["Background"].inputs["Strength"].default_value=0
ultra=bpy.data.materials["Diffusion 5 | Ultrabounce"]
bpy.ops.mesh.primitive_plane_add(size=4,location=(0,3,1.8),rotation=(math.pi/2,0,0))
bounce=bpy.context.object;bounce.name="Test bounce";bounce.data.materials.append(ultra)
mat=bpy.data.materials.new("Test floor");mat.use_nodes=True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.5,.5,.5,1)
bpy.ops.mesh.primitive_plane_add(size=12)
bpy.context.object.data.materials.append(mat)
bpy.ops.object.camera_add(location=(4,-5,3))
camera=bpy.context.object;camera.rotation_euler=(Vector((0,1,1))-camera.location).to_track_quat("-Z","Y").to_euler()
camera.data.lens=38;s.camera=camera
s.view_layers[0].use_pass_diffuse_indirect=True
s.use_nodes=True
# Blender 5 compositor API
tree=s.node_tree if hasattr(s,"node_tree") else None
if tree is None:
    tree=bpy.data.node_groups.new("Test compositor","CompositorNodeTree")
    s.compositing_node_group=tree
    tree.interface.new_socket(name="Image",in_out="OUTPUT",socket_type="NodeSocketColor")
    out=tree.nodes.new("NodeGroupOutput")
else:
    tree.nodes.clear();out=tree.nodes.new("CompositorNodeComposite")
rl=tree.nodes.new("CompositorNodeRLayers")
tree.links.new(next(x for x in rl.outputs if "indirect" in x.name.lower() and "diffuse" in x.name.lower()),out.inputs["Image"])
m=next(m for m in o.modifiers if m.type=="NODES")
results={}
black=bpy.data.materials.new("Test black bounce")
black.use_nodes=True
bn=black.node_tree.nodes
bn.clear()
bd=bn.new("ShaderNodeBsdfDiffuse")
bd.inputs["Color"].default_value=(0,0,0,1)
bo=bn.new("ShaderNodeOutputMaterial")
black.node_tree.links.new(bd.outputs[0],bo.inputs["Surface"])
spot_data=bpy.data.lights.new("Test standard spot","SPOT")
spot=bpy.data.objects.new("Test standard spot",spot_data)
s.collection.objects.link(spot)
for mode in ["Bare","Reflector","Fresnel","Octobox","StandardSpot"]:
  for surface in ["Ultrabounce","Black","NativeOff"]:
    spot.hide_render=True
    o.hide_render=False
    light.hide_render=False
    area.hide_render=False
    bounce.data.materials[0]=black if surface=="Black" else ultra
    m.properties.inputs.Socket_10.value=mode if mode!="StandardSpot" else "Fresnel"
    o.update_tag();bpy.context.view_layer.update()
    if mode=="StandardSpot":
        evaluated=light.evaluated_get(bpy.context.evaluated_depsgraph_get())
        spot.matrix_world=evaluated.matrix_world.copy()
        spot_data.energy=evaluated.data.energy
        spot_data.spot_size=evaluated.data.spot_size
        spot_data.spot_blend=evaluated.data.spot_blend
        spot_data.shadow_soft_size=evaluated.data.shadow_soft_size
        light.hide_render=True
        area.hide_render=True
        o.hide_render=True
        spot.hide_render=False
    if surface=="NativeOff":
        light.hide_render=True
        area.hide_render=True
        spot.hide_render=True
    if mode!="StandardSpot" and surface=="Ultrabounce":
        dg=bpy.context.evaluated_depsgraph_get()
        active=[x for x in (light,area) if x.evaluated_get(dg).data.energy>0]
        assert len(active)==1, (mode, "expected exactly one powered native source")
        for x in (light,area):
            for owner in (x,x.data,x.data.node_tree):
                if owner and owner.animation_data:
                    assert all(d.driver.is_valid for d in owner.animation_data.drivers), (mode,x.name)
    label=mode+"_"+surface
    s.render.image_settings.file_format="OPEN_EXR"
    s.render.filepath=str(output_dir/(label+".exr"))
    bpy.ops.render.render(write_still=True)
    im=bpy.data.images.load(s.render.filepath,check_existing=False)
    vals=list(im.pixels)
    rgb=[v for i,v in enumerate(vals) if i%4!=3]
    results[label]={"indirect_mean":sum(rgb)/len(rgb),"indirect_max":max(rgb)}
    print("BOUNCE_RESULT",label,results[label],flush=True)
    bpy.data.images.remove(im)
for mode in ["Bare","Reflector","Fresnel","Octobox"]:
    white=results[mode+"_Ultrabounce"]["indirect_mean"]
    black=results[mode+"_Black"]["indirect_mean"]
    off=results[mode+"_NativeOff"]["indirect_max"]
    assert white>10*black and white>0.001, (mode,"missing bounce",white,black)
    assert off<1e-6, (mode,"mesh is still emitting",off)
reference=results["StandardSpot_Ultrabounce"]["indirect_mean"]
assert abs(results["Fresnel_Ultrabounce"]["indirect_mean"]/reference-1)<0.05
(output_dir/"results.json").write_text(json.dumps(results,indent=2))
print("PASS: native sources, valid drivers, bounce, no mesh contribution. Results:",output_dir)
