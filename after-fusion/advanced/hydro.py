"""Atlas radiating-gas solver 0.1: spherical Euler + optically-thin free-free loss.
Prescribed expanding post-pulse reference cloud, NOT target implosion/burn design.
First-order Rusanov finite volume, ideal fully ionized Z=1 gas, Ti=Te.
Radiated energy escapes; no opacity/reabsorption/radiation pressure/laser drive.
"""
from pathlib import Path
import numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
GAMMA=5/3;KB=1.380649e-23;MP=1.67262192369e-27;MEAN_ION_MASS=2.5*MP
CV=3*KB/MEAN_ION_MASS;EV_K=8.617333262145e-5;BREMS=1.69e-38

def run(n=640,write=True):
 edges=np.linspace(0,.002,n+1);r=(edges[:-1]+edges[1:])/2;vol=4*np.pi/3*np.diff(edges**3);area=4*np.pi*edges**2;dr=edges[1]
 profile=np.exp(-(r/.00022)**8);rho=.02+9.98*profile;temp=1e6+5e6*profile
 U=np.column_stack((rho,np.zeros(n),rho*CV*temp));initial=float(np.sum(U[:,2]*vol));mass0=float(np.sum(U[:,0]*vol))
 time=0;lost=0;outflow=0;massflow=0;steps=0;snapshots=[]
 times=np.r_[0,np.geomspace(1e-12,8e-9,120)];tracer=np.linspace(0,.0012,120)
 def primitives(u):
  density=u[:,0];velocity=u[:,1]/density;pressure=(GAMMA-1)*(u[:,2]-.5*density*velocity**2)
  return density,velocity,pressure
 def snapshot():
  d,v,p=primitives(U);T=p/(GAMMA-1)/(d*CV)
  return {'timeS':float(time),'rhoKgM3':d.tolist(),'velocityMS':v.tolist(),'temperatureK':T.tolist(),'tracerRadiusM':tracer.tolist(),'gasEnergyJ':float(np.sum(U[:,2]*vol)),'radiatedJ':lost,'outflowJ':outflow}
 snapshots.append(snapshot())
 for target in times[1:]:
  while time<target:
   d,v,p=primitives(U);assert np.all(p>0) and np.all(d>0)
   sound=np.sqrt(GAMMA*p/d);dt=min(.32*dr/np.max(abs(v)+sound),target-time)
   left=U[0].copy();left[1]*=-1
   ghost=np.vstack([left,U,U[-1]])
   dg,vg,pg=primitives(ghost);cg=np.sqrt(GAMMA*pg/dg)
   flux=np.column_stack((ghost[:,1],ghost[:,1]*vg+pg,(ghost[:,2]+pg)*vg))
   speed=np.maximum(abs(vg[:-1])+cg[:-1],abs(vg[1:])+cg[1:])
   F=.5*(flux[:-1]+flux[1:])-.5*speed[:,None]*(ghost[1:]-ghost[:-1])
   du=-(area[1:,None]*F[1:]-area[:-1,None]*F[:-1])/vol[:,None]
   du[:,1]+=p*np.diff(area)/vol
   U+=dt*du
   outflow+=float(dt*area[-1]*F[-1,2]);massflow+=float(dt*area[-1]*F[-1,0])
   d,v,p=primitives(U);internal=U[:,2]-.5*d*v*v
   if np.any(internal<=0):raise RuntimeError('Nonpositive internal energy')
   # Analytic cooling substep for du/dt=-C sqrt(u), conserving escaped radiation.
   ni=d/MEAN_ION_MASS;coefficient=BREMS*ni**2*np.sqrt(EV_K/(d*CV))
   cooled=np.maximum(0,np.sqrt(internal)-.5*coefficient*dt)**2
   emitted=internal-cooled;U[:,2]-=emitted;lost+=float(np.sum(emitted*vol))
   tracer+=dt*np.interp(tracer,r,v,left=0,right=v[-1]);time+=dt;steps+=1
  snapshots.append(snapshot())
 residual=(snapshots[-1]['gasEnergyJ']+lost+outflow-initial)/initial
 massres=(float(np.sum(U[:,0]*vol))+massflow-mass0)/mass0
 result={'schema':'ife-radiating-hydro/1','solver':'Atlas spherical radiating-gas FV','version':'0.1','spatialCells':n,'radiusEdgesM':edges.tolist(),'radiusM':r.tolist(),'snapshots':snapshots,'model':'spherical Euler; ideal fully ionized Z=1 gas; mean ion mass 2.5 mp; Ti=Te; optically thin bremsstrahlung energy loss','boundary':'reflecting origin; zero-gradient outflow at 2 mm','initialCondition':'prescribed 0.22 mm hot cloud; rho 10 vs 0.02 kg/m3; T 6e6 vs 1e6 K; zero velocity. Illustrative post-pulse state, no simulated implosion or fusion rate.','initialEnergyJ':initial,'energyResidualRelative':residual,'massResidualRelative':massres,'steps':steps,'omissions':['laser drive','fusion burn and rates','alpha stopping','tabulated EOS','radiation absorption and pressure','electron conduction','3D instabilities'],'radiationModel':'Optically thin escaping power: 1.69e-38 Z^2 ni ne sqrt(Te[eV]) W/m3; nonrelativistic, prescribed ionization.'}
 assert abs(residual)<1e-10 and abs(massres)<1e-10
 if write:
  (ROOT/'public/data/hydro.json').write_text(json.dumps(result,separators=(',',':')))
 return result
if __name__=='__main__':
 fine=run();coarse=run(320,False)
 a=np.array(fine['snapshots'][-1]['temperatureK']);b=np.interp(fine['radiusM'],coarse['radiusM'],coarse['snapshots'][-1]['temperatureK'])
 report={k:v for k,v in fine.items() if k not in ['snapshots','radiusM','radiusEdgesM']};report['coarseFineTemperatureRelativeL1']=float(np.sum(np.abs(a-b))/np.sum(abs(a)));report['scope']='conservation and resolution checks, not experimental validation';report['radiatedJ']=fine['snapshots'][-1]['radiatedJ']
 (ROOT/'evidence/hydro-run.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
