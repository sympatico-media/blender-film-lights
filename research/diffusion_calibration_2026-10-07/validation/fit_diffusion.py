# SPDX-License-Identifier: GPL-3.0-or-later
#
# Fits the diffusion/scatter material coefficients in fit_parameters.json from the
# synthetic rig renders produced by build_test_rig.py (run that script first to
# generate the .npy arrays this script reads).
from pathlib import Path
import numpy as np,json,math
r=Path(__file__).resolve().parent
x=-1.1+(np.arange(512)+.5)*3.6/512
p={k:(np.load(r/(k+'.npy'))[:,:,:3]@np.array([.2126,.7152,.0722]))[56:72].mean(0) for k in ['direct_open','direct_shadow','scatter_open','scatter_shadow']}
def sample(k,xx):return float(p[k][np.abs(x-xx)<.025].mean())
base=sample('direct_open',-.7);K=sample('scatter_open',-.7)/base
# Published 10/20 degree readings are absolute EV; wrap coordinates are wall offsets from flag edge.
B=np.array([sample('scatter_shadow',3.048*math.tan(math.radians(a)))/base for a in (10,20)])
def cct_rgb(T):
 # Planckian-locus xy approximation; chromaticity-only RGB filter approximation, not spectrum.
 xx=-.2661239e9/T**3-.2343580e6/T**2+.8776956e3/T+.179910
 yy=-.9549476*xx**3-1.37418593*xx**2+2.09137015*xx-.16748867
 xyz=np.array([xx/yy,1,(1-xx-yy)/yy])
 return np.array([[3.2406,-1.5372,-.4986],[-.9689,1.8758,.0415],[.0557,-.2040,1.0570]])@xyz
specs=[
 ('Diffusion 2 | Silk',1.9,(7.4,6.1),3210,[.11466]*3,'TRP White Polysilk (133)',53),
 ('Diffusion 3 | Half Silk',1.1,(7.7,6.2),3220,[.0702]*3,'TRP White China Silk (736)',28),
 ('Diffusion 4 | Quarter Silk',1.0,(7.2,5.9),3200,[.0351]*3,'TRP White Quarter Silk (074)',26),
 ('Diffusion 6 | 215 Half Tough Spun',-math.log2(.36),None,None,[.229632]*3,'LEE 215 Half Tough Spun, legacy brochure',36),
 ('Diffusion 7 | 250 Half White Diffusion',.8,(7.6,5.7),3190,[.156288]*3,'LEE 250 in TRP test',20),
 ('Diffusion 8 | Opal Frost',-math.log2(.71),None,None,[.0651]*3,'LEE 410 Opal Frost, manufacturer Y=71%',None),
 ('Diffusion 9 | Unbleached Muslin',2.7,(6.9,5.5),3040,[.6396,.5304,.3666],'TRP Unbleached Muslin (585)',65),
 ('Diffusion 10 | Bleached Muslin',3.2,(6.7,5.4),3050,[.7216,.7052,.6642],'TRP Bleached Muslin (610)',67)]
out={}
for name,loss,evs,temp,reflect,product,page in specs:
 tint=np.ones(3) if temp is None else cct_rgb(temp)/cct_rgb(3250)
 # Unit luminance under neutral RGB white. Temp fit is approximate and constrained to 3250 K reference.
 tint/=np.dot(tint,[.2126,.7152,.0722])
 target=2**-loss
 ss=np.linspace(0,target/K,10001);dd=target-K*ss
 valid=np.all((ss+dd)[:,None]*tint+np.array(reflect)<=1+1e-8,axis=1)
 if evs:
  bt=2**(np.array(evs)-11.3)
  err=np.mean((np.log2(np.maximum(ss[:,None]*B,1e-9)/bt))**2,axis=1)
 else:
  # Scattering proportion is a qualitative assumption for gel materials without a measured profile.
  desired=.16 if '215' in name else .12
  err=(ss-desired)**2
 err[~valid]=np.inf
 i=int(err.argmin());assert np.isfinite(err[i])
 d=float(dd[i]);sc=float(ss[i]);out[name]={'reference_product':product,'pdf_page_1based':page,'target_loss_stops':loss,'direct':d,'scattered':sc,'transmission_tint':tint.tolist(),'reflection_rgb':reflect,'reference_CCT_in':3250 if temp else None,'reference_CCT_out':temp,'predicted_loss_stops':-math.log2(d+K*sc),'predicted_shadow_ev_10_20':(11.3+np.log2(np.maximum(sc*B,1e-12))).tolist(),'reference_shadow_ev_10_20':evs,'max_channel_energy':float(np.max((d+sc)*tint+reflect))}
(r/'fit_parameters.json').write_text(json.dumps({'model':'energy-bounded transparent + Lambertian transmitted + Lambertian reflected closure','rig_status':'Published distances; approximate source; fitted central exposure and least-squares shadow falloff. Not exact manufacturer reproduction.','diffuse_basis_open_ratio':K,'shadow_basis_ratios':B.tolist(),'presets':out},indent=2))
for name,v in out.items():print(name, 'D/S',round(v['direct'],3),round(v['scattered'],3),'energy',round(v['max_channel_energy'],3),'shadow',np.round(v['predicted_shadow_ev_10_20'],2))
