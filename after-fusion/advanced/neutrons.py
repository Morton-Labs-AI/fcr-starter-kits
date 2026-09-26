"""Actual OpenMC 0.15.3 n+photon transport, normalized per source neutron.
A deliberately simple water-cooled test blanket; not a breeding blanket design.
Requires OpenMC 0.15.3 and the separately acquired nuclear data. All lengths in OpenMC are cm.
"""
from pathlib import Path
import openmc,numpy as np,json,hashlib,xml.etree.ElementTree as ET,os
ROOT=Path(__file__).resolve().parents[1];RUN=ROOT/'tmp/ife-showcase-solver/neutrons';RUN.mkdir(parents=True,exist_ok=True);os.chdir(RUN)
fe=openmc.Material(1,'Fe56 first-wall surrogate');fe.add_nuclide('Fe56',1);fe.set_density('g/cm3',7.87)
water=openmc.Material(2,'H1 O16 water test blanket');water.add_nuclide('H1',2);water.add_nuclide('O16',1);water.set_density('g/cm3',.998);water.add_s_alpha_beta('c_H_in_H2O')
r0=openmc.Sphere(r=600);r1=openmc.Sphere(r=602);r2=openmc.Sphere(r=650,boundary_type='vacuum')
void=openmc.Cell(1,region=-r0);wall=openmc.Cell(2,fill=fe,region=+r0&-r1);blanket=openmc.Cell(3,fill=water,region=+r1&-r2)
settings=openmc.Settings();settings.run_mode='fixed source';settings.batches=32;settings.particles=2000;settings.seed=24092026
settings.photon_transport=True;settings.electron_treatment='led';settings.temperature={'default':293.6,'method':'nearest','tolerance':10}
source=openmc.IndependentSource(space=openmc.stats.Point((0,0,0)),angle=openmc.stats.Isotropic(),energy=openmc.stats.Discrete([14.1e6],[1]),time=openmc.stats.Discrete([0],[1]));settings.source=source
settings.track=[(1,1,i) for i in range(1,193)];settings.max_tracks=1000
edges=np.r_[0,np.linspace(600,602,17),np.linspace(603,650,48)]
mesh=openmc.SphericalMesh(r_grid=edges,theta_grid=[0,np.pi],phi_grid=[0,2*np.pi])
radial=openmc.Tally(1,'radial deposited energy');radial.filters=[openmc.MeshFilter(mesh)];radial.scores=['heating'];radial.estimator='collision'
materials=openmc.Tally(2,'material heating');materials.filters=[openmc.CellFilter([wall,blanket])];materials.scores=['heating'];materials.estimator='collision'
model=openmc.Model(openmc.Geometry([void,wall,blanket]),openmc.Materials([fe,water]),settings,openmc.Tallies([radial,materials]));model.export_to_xml();model.run(threads=4)
sp=openmc.StatePoint('statepoint.32.h5');tally=sp.get_tally(id=1);cell=sp.get_tally(id=2)
tracks=[]
for history in openmc.Tracks('tracks.h5'):
 for secondary,pt in enumerate(history.particle_tracks):
  if pt.particle.name.lower() not in ['neutron','photon']:continue
  states=pt.states
  points=[]
  for s in states:
   points.append([float(s['r']['x'])/100,float(s['r']['y'])/100,float(s['r']['z'])/100,float(s['time']),float(s['E'])])
  if len(points)>1:tracks.append({'history':list(history.identifier),'secondary':secondary,'species':pt.particle.name.lower(),'states':points})
xs=Path(openmc.config['cross_sections']);data=[]
for e in ET.parse(xs).getroot().findall('library'):
 if e.attrib.get('materials') in ['H1','O16','Fe56','H','O','Fe','c_H_in_H2O'] and e.attrib.get('type')!='wmp':
  p=xs.parent/e.attrib['path'];data.append({**e.attrib,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
out={'schema':'ife-neutrons/1','solver':'OpenMC','version':openmc.__version__,'seed':settings.seed,'histories':settings.batches*settings.particles,'batches':settings.batches,'source':{'energyEv':14.1e6,'positionM':[0,0,0],'timeS':0,'angularDistribution':'isotropic','normalization':'per source neutron; prescribed emission, no fusion-rate calculation'},'geometry':{'voidRadiusM':6,'wallOuterM':6.02,'blanketOuterM':6.5,'wall':'pure Fe56 surrogate, 7870 kg/m3','blanket':'H1/O16 water, 998 kg/m3, S(alpha,beta)','outerBoundary':'vacuum'},'transport':'continuous-energy neutron + photon; secondary electron energy deposited locally','data':data,'radiusEdgesM':(edges/100).tolist(),'heatingEvPerSource':tally.mean.ravel().tolist(),'heatingStdDev':tally.std_dev.ravel().tolist(),'materialHeatingEv':cell.mean.ravel().tolist(),'materialHeatingStdDev':cell.std_dev.ravel().tolist(),'tracks':tracks,'tracksNote':'Actual recorded source histories and progeny; first 192 source IDs, no trajectories inferred from tallies. Display subset does not determine heating.'}
(ROOT/'public/data/neutrons.json').write_text(json.dumps(out,separators=(',',':')))
summary={k:v for k,v in out.items() if k!='tracks'};summary['savedParticleTracks']=len(tracks);summary['statepointSha256']=hashlib.sha256(Path('statepoint.32.h5').read_bytes()).hexdigest();summary['tracksSha256']=hashlib.sha256(Path('tracks.h5').read_bytes()).hexdigest()
(ROOT/'evidence/neutron-run.json').write_text(json.dumps(summary,indent=2)+'\n')
print('EXPORTED',len(tracks),'particle tracks; heating eV/source',out['materialHeatingEv'])
