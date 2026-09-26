export const clamp=(x:number)=>Math.max(0,Math.min(1,x));
export const smooth=(x:number)=>{const u=clamp(x);return u*u*u*(10+u*(-15+6*u));};
const nodes=[[0,390],[2.8,100],[3.8,15],[4.6,.025],[5.1,.0016],[5.6,2.0e-9],[6.5,1.4e-9],[7.25,.0058],[8.5,.010],[9.6,17],[10.8,17],[12.1,.20],[12.8,.25],[14,75],[15,125]];
const logs=nodes.map(n=>Math.log(n[1]));
const slopes=nodes.slice(1).map((n,i)=>(logs[i+1]-logs[i])/(n[0]-nodes[i][0]));
const tangent=logs.map((_,i)=>i===0?slopes[0]:i===logs.length-1?slopes[i-1]:slopes[i-1]*slopes[i]<=0?0:2/(1/slopes[i-1]+1/slopes[i]));
function distanceAt(t:number){let i=0;while(i<nodes.length-2&&t>nodes[i+1][0])i++;const h=nodes[i+1][0]-nodes[i][0],u=clamp((t-nodes[i][0])/h);return Math.exp((2*u**3-3*u*u+1)*logs[i]+(u**3-2*u*u+u)*h*tangent[i]+(-2*u**3+3*u*u)*logs[i+1]+(u**3-u*u)*h*tangent[i+1]);}
export function poseAt(t:number){
 const distance=distanceAt(t),focus:[number,number,number]=[0,0,0];
 const wall=smooth((t-10.75)/1.35),returnPlant=smooth((t-12.8)/2.2);
 const focusReturn=smooth((t-13.3)/1.7);
 focus[0]=6.01*wall*(1-focusReturn)-10*focusReturn;focus[1]=-5*focusReturn;focus[2]=-48*focusReturn;
 const opening=1-Math.exp(-Math.pow(distance/180,1.8));
 const azimuth=.829*opening*(1-smooth((t-3)/1))+2.55*returnPlant,elevation=.47*opening*(1-smooth((t-3)/1))+.5*returnPlant;
 let physicalTimeS=0;
 if(t>=6.5&&t<=8.5)physicalTimeS=8e-9*((t-6.5)/2)**2;
 else if(t>8.5&&t<=10.8)physicalTimeS=8e-9*Math.pow(2e-6/8e-9,(t-8.5)/2.3);
 else if(t>10.8&&t<=12.1)physicalTimeS=2e-6*Math.pow(.01/2e-6,(t-10.8)/1.3);
 else if(t>12.1&&t<=12.9)physicalTimeS=.01*Math.pow(30/.01,(t-12.1)/.8);
 else if(t>12.9)physicalTimeS=30*Math.pow(600/30,(t-12.9)/2.1);
 return {distance,focus,azimuth,elevation,physicalTimeS,cameraTimeS:t,react:smooth((t-5.15)/.3)*(1-smooth((t-6.6)/.45)),gas:smooth((t-6.7)/.4)*(1-smooth((t-8.55)/.7)),transport:smooth((t-8.7)/.5)*(1-smooth((t-11.4)/.8)),thermal:smooth((t-10.8)/.6),plantReturn:returnPlant};
}
