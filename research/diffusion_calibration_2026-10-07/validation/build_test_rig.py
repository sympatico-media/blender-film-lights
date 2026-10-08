# SPDX-License-Identifier: GPL-3.0-or-later
#
# Builds a synthetic Cycles rig (fabric, flag, wall, area light) and renders the
# direct/scattered, open/shadow passes used by fit_diffusion.py. Run with Blender's
# background Python: `blender -b --python build_test_rig.py`.
import bpy,math,json
from pathlib import Path
from mathutils import Vector
import numpy as np
R=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=128;s.cycles.use_denoising=False;s.cycles.max_bounces=8;s.cycles.diffuse_bounces=4;s.cycles.transmission_bounces=8;s.cycles.transparent_max_bounces=16
s.world=bpy.data.worlds.new('Black laboratory');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0
s.render.resolution_x=512;s.render.resolution_y=128;s.render.resolution_percentage=100;s.render.image_settings.file_format='OPEN_EXR';s.render.image_settings.color_depth='32'
s.view_settings.view_transform='Standard'
def mat(name,typ,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();b=n.new(typ);b.inputs['Color'].default_value=(*color,1);o=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(b.outputs[0],o.inputs['Surface']);return m
white=mat('Receiver','ShaderNodeBsdfDiffuse',(.8,)*3);black=mat('Black','ShaderNodeBsdfDiffuse',(0,)*3)
def plane(name,loc,scale,m):
 bpy.ops.mesh.primitive_plane_add(size=2,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(m);return o
wall=plane('Wall 10ft beyond flag',(0,0,-5.1816),(5,2,1),white)
fab=plane('Four foot diffusion',(0,0,-.9144),(.6096,.6096,1),white)
flag=plane('Four foot flag, edge on axis',(.6096,0,-2.1336),(.6096,.6096,1),black)
bpy.ops.object.light_add(type='AREA',location=(0,0,0));lamp=bpy.context.object;lamp.data.energy=100;lamp.data.shape='DISK';lamp.data.size=.08
bpy.ops.object.camera_add(location=(.7,0,-4));cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=3.6;s.camera=cam
# Pixel coordinates cover x[-1.1,2.5], y[-.45,.45]. Camera looks down -Z.
meta={'source_to_fabric_m':.9144,'fabric_to_flag_m':1.2192,'flag_to_wall_m':3.048,'source':'80 mm Lambertian area disk; approximation to published open-eye 2K fixture','camera_xmin':-1.1,'camera_xmax':2.5,'resolution':[512,128]}
for name,typ in [('direct','ShaderNodeBsdfTransparent'),('scatter','ShaderNodeBsdfTranslucent')]:
 fab.data.materials[0]=mat(name,typ,(1,1,1))
 for blocked in [False,True]:
  flag.hide_render=not blocked
  key=name+('_shadow' if blocked else '_open');s.render.filepath=str(R/(key+'.exr'));bpy.ops.render.render(write_still=True)
  im=bpy.data.images.load(s.render.filepath,check_existing=False);a=np.array(im.pixels[:]).reshape(128,512,4);np.save(R/(key+'.npy'),a);bpy.data.images.remove(im)
(R/'rig.json').write_text(json.dumps(meta,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(R/'Calibration_Rig.blend'))
print('BASIS_DONE')
