export type HydroFrame={timeS:number;rhoKgM3:number[];velocityMS:number[];temperatureK:number[];tracerRadiusM:number[];gasEnergyJ:number;radiatedJ:number;outflowJ:number};
export type Hydro={radiusM:number[];snapshots:HydroFrame[];spatialCells:number;initialEnergyJ:number};
export type Track={history:number[];secondary:number;species:'neutron'|'photon';states:number[][]};
export type Neutrons={tracks:Track[];radiusEdgesM:number[];heatingEvPerSource:number[];heatingStdDev:number[];histories:number;version:string;materialHeatingEv:number[]};
export type ThermalFrame={timeS:number;wallDeltaKPerSource:number[];coolantDeltaKPerSource:number;exchangerEnergyJPerSource:number;remainingEnergyJPerSource:number};
export type Thermal={wallRadiusM:number[];snapshots:ThermalFrame[];temperatureNormalizationKPerSource:number;coolantNormalizationKPerSource:number;initialEnergyJPerSource:number};
export function bracket<T extends {timeS:number}>(a:T[],t:number):[T,T,number]{let i=0;while(i<a.length-2&&a[i+1].timeS<t)i++;const j=Math.min(i+1,a.length-1),u=Math.max(0,Math.min(1,(t-a[i].timeS)/(a[j].timeS-a[i].timeS)));return[a[i],a[j],u];}
export const blend=(a:number,b:number,u:number)=>a+(b-a)*u;
