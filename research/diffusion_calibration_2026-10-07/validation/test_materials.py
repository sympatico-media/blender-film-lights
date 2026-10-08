# SPDX-License-Identifier: GPL-3.0-or-later
#
# Historical validation record, not a runnable script in this repository: it
# depends on `update_reference_diffusions.py` (the development script that
# applied the fitted coefficients to the live material library) and on a
# "Before_Reference_Diffusion_Update.blend" snapshot taken immediately before
# that update. Both were local development artifacts and are not included here.
# Kept so the before/after validation methodology and its acceptance threshold
# (0.12 stop max exposure error, see render_validation.json) are documented.
import bpy,sys,json,math
from pathlib import Path
import numpy as np
V=Path(__file__).resolve().parent
R=V.parent.parent.parent
sys.path.insert(0,str(R));import update_reference_diffusions as upd
bpy.ops.wm.open_mainfile(filepath=str(V/'Calibration_Rig.blend'))
with bpy.data.libraries.load(str(R/'Before_Reference_Diffusion_Update.blend'),link=False) as (src,dst):dst.materials=list(upd.PARAMS['presets'])
s=bpy.context.scene;s.cycles.samples=256
fab=bpy.data.objects['Four foot diffusion'];flag=bpy.data.objects['Four foot flag, edge on axis']
x=-1.1+(np.arange(512)+.5)*3.6/512;mask=np.abs(x+.7)<.025
base=float((np.load(V/'direct_open.npy')[56:72,:,:3]@np.array([.2126,.7152,.0722]))[:,mask].mean())
def render(key):
 s.render.filepath=str(V/(key+'.exr'));bpy.ops.render.render(write_still=True)
 im=bpy.data.images.load(s.render.filepath,check_existing=False);a=np.array(im.pixels[:]).reshape(128,512,4);bpy.data.images.remove(im);return a
report={}
for j,(name,p) in enumerate(upd.PARAMS['presets'].items()):
 m=bpy.data.materials[name];fab.data.materials[0]=m;flag.hide_render=True
 old=render('old_%02d'%j);oldY=float((old[56:72,:,:3]@np.array([.2126,.7152,.0722]))[:,mask].mean())
 upd.update_material(m,p)
 new=render('new_%02d'%j);newY=float((new[56:72,:,:3]@np.array([.2126,.7152,.0722]))[:,mask].mean())
 flag.hide_render=False;sh=render('shadow_%02d'%j);prof=(sh[56:72,:,:3]@np.array([.2126,.7152,.0722])).mean(0)
 evs=[11.3+math.log2(float(prof[np.abs(x-3.048*math.tan(math.radians(a)))<.025].mean())/base) for a in (10,20)]
 loss=-math.log2(newY/base);oldloss=-math.log2(oldY/base)
 report[name]={'target_loss':p['target_loss_stops'],'old_loss':oldloss,'new_loss':loss,'error_stops':loss-p['target_loss_stops'],'shadow_ev_10_20':evs,'reference_shadow_ev_10_20':p['reference_shadow_ev_10_20']}
 assert abs(loss-p['target_loss_stops'])<.12,(name,report[name])
 print('MATERIAL_VALIDATED',name,json.dumps(report[name]),flush=True)
(V/'render_validation.json').write_text(json.dumps({'status':'passed','linear_EXR':True,'denoising':False,'samples':256,'max_allowed_exposure_error_stops':.12,'measurements':report},indent=2))
print('ALL_MATERIALS_PASSED',flush=True)
