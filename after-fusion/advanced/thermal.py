"""Transient first-wall conduction + well-mixed water + exchanger sink.
Input: actual OpenMC radial heating, normalized to one incident source neutron.
No guessed absolute fusion yield. Linear perturbation about 293.6 K.
"""
from pathlib import Path
import numpy as np,json
from scipy.linalg import solve_banded
ROOT=Path(__file__).resolve().parents[1]
EV=1.602176634e-19

def solve(n=80,scale=1):
 neutron=json.loads((ROOT/'public/data/neutrons.json').read_text());r=np.linspace(6,6.02,n+1);rc=(r[1:]+r[:-1])/2;vol=4*np.pi/3*np.diff(r**3)
 capacities=np.r_[7870*449*vol,998*4182*4*np.pi/3*(6.5**3-6.02**3)]
 # Interpolate integrated deposition, not noisy pointwise power density.
 old=np.array(neutron['radiusEdgesM']);energy=np.array(neutron['heatingEvPerSource'])*EV*scale;cdf=np.r_[0,np.cumsum(energy)]
 wallenergy=np.diff(np.interp(r,old,cdf));waterenergy=np.interp(6.5,old,cdf)-np.interp(6.02,old,cdf)
 initial=np.r_[wallenergy,waterenergy]/capacities;temp=initial.copy()
 conductance=80*4*np.pi*r[1:-1]**2/np.diff(rc)
 film=8000*4*np.pi*6.02**2;UA=5e6
 # C dT/dt = -L T; implicit Euler preserves positivity and tracks exchanger heat.
 conductance=np.r_[conductance,film];diag=np.r_[conductance,0]+np.r_[0,conductance];diag[-1]+=UA
 time=0;removed=0;initialenergy=float(np.sum(initial*capacities));frames=[];times=np.r_[0,np.geomspace(1e-6,600,179)]
 def save():return {'timeS':float(time),'wallDeltaKPerSource':temp[:-1].tolist(),'coolantDeltaKPerSource':float(temp[-1]),'exchangerEnergyJPerSource':removed,'remainingEnergyJPerSource':float(np.sum(capacities*temp))}
 frames.append(save())
 for goal in times[1:]:
  while time<goal:
   dt=min(max(.001,goal*.008),goal-time)
   bands=np.zeros((3,n+1));bands[1]=capacities+dt*diag;bands[0,1:]=-dt*conductance;bands[2,:-1]=-dt*conductance
   temp=solve_banded((1,1),bands,capacities*temp);removed+=dt*UA*temp[-1];time+=dt
  frames.append(save())
 residual=(removed+np.sum(capacities*temp)-initialenergy)/initialenergy
 assert abs(residual)<1e-9 and np.all(temp>=0)
 return {'schema':'ife-thermal/1','solver':'Atlas spherical conduction + lumped coolant','version':'0.1','wallRadiusM':rc.tolist(),'wallEdgesM':r.tolist(),'snapshots':frames,'initialEnergyJPerSource':initialenergy,'temperatureNormalizationKPerSource':float(initial.max()),'coolantNormalizationKPerSource':float(max(f['coolantDeltaKPerSource'] for f in frames)),'energyResidualRelative':float(residual),'assumptions':{'ironConductivityWmK':80,'ironCpJkgK':449,'ironDensityKgM3':7870,'waterCpJkgK':4182,'waterDensityKgM3':998,'filmWm2K':8000,'exchangerUAWK':UA,'boundary':'inner wall adiabatic; outer wall convection to well-mixed blanket; exchanger to fixed zero-perturbation reservoir','backgroundK':293.6,'source':'OpenMC integrated n+photon heating, instantaneous deposition relative to thermal times; one source neutron','flow':'well-mixed coolant, not CFD; film and UA are scenario assumptions'}}
if __name__=='__main__':
 result=solve();coarse=solve(40);scaled=solve(80,2)
 assert np.allclose(np.array(result['snapshots'][-1]['wallDeltaKPerSource'])*2,scaled['snapshots'][-1]['wallDeltaKPerSource'],rtol=1e-10,atol=0)
 fine=result['snapshots'][120]['wallDeltaKPerSource'];c=np.interp(result['wallRadiusM'],coarse['wallRadiusM'],coarse['snapshots'][120]['wallDeltaKPerSource'])
 report={k:v for k,v in result.items() if k not in ['snapshots','wallEdgesM','wallRadiusM']};report['gridCheckRelativeL1']=float(np.sum(abs(np.array(fine)-c))/np.sum(abs(np.array(fine))));report['sourceScalingCheck']='factor-of-two linearity passed'
 (ROOT/'public/data/thermal.json').write_text(json.dumps(result,separators=(',',':')))
 (ROOT/'evidence/thermal-run.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
