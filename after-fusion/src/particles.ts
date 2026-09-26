import * as T from 'three';
import { type Neutrons, blend, bracket, type Hydro } from './data.ts';
import { smooth, clamp } from './journey.ts';

/** Every transport segment comes from the OpenMC track file, interpolated in flight time. */
export function transportTracks(data:Neutrons){
 const root=new T.Group();
 const disc=document.createElement('canvas');disc.width=disc.height=32;const context=disc.getContext('2d')!;context.fillStyle='white';context.beginPath();context.arc(16,16,14,0,Math.PI*2);context.fill();const map=new T.CanvasTexture(disc);
 const families=new Set(data.tracks.filter(t=>t.secondary===0&&t.states.length>1&&t.states[1][2]<0).slice(0,64).map(t=>t.history.join(':')));
 const selected=data.tracks.filter(t=>families.has(t.history.join(':')));
 const groups=(['neutron','photon'] as const).map(species=>{
  const tracks=selected.filter(t=>t.species===species),vertices=new Float32Array(tracks.reduce((n,t)=>n+t.states.length,0)*6),heads=new Float32Array(tracks.length*3);
  const geometry=new T.BufferGeometry().setAttribute('position',new T.BufferAttribute(vertices,3));
  const material=new T.LineBasicMaterial({color:species==='neutron'?'#83dcf2':'#ffbe66',transparent:true,opacity:0,depthWrite:false});
  const lines=new T.LineSegments(geometry,material);lines.frustumCulled=false;
  const pointsGeo=new T.BufferGeometry().setAttribute('position',new T.BufferAttribute(heads,3));
  const pointsMat=new T.PointsMaterial({color:species==='neutron'?'#d6f7ff':'#ffe2ad',size:4,map,alphaTest:.25,sizeAttenuation:false,transparent:true,depthWrite:false});
  const points=new T.Points(pointsGeo,pointsMat);points.frustumCulled=false;root.add(lines,points);
  return {tracks,vertices,heads,geometry,material,pointsGeo,pointsMat};
 });
 function update(time:number,opacity:number){root.visible=opacity>0;let active=0;
  for(const g of groups){let n=0,h=0;const tail=Math.max(35e-9,time*.6);
   for(const track of g.tracks){const s=track.states;
    for(let i=1;i<s.length;i++){
     const a=s[i-1],b=s[i],dt=b[3]-a[3];if(dt<=0||a[3]>time||b[3]<time-tail)continue;
     const lo=clamp((time-tail-a[3])/dt),hi=clamp((time-a[3])/dt);if(hi<=lo)continue;
     for(const u of [lo,hi])for(let j=0;j<3;j++)g.vertices[n++]=blend(a[j],b[j],u);
     if(a[3]<=time&&time<b[3]){for(let j=0;j<3;j++)g.heads[h++]=blend(a[j],b[j],hi);active++;}
    }
   }
   g.geometry.setDrawRange(0,n/3);g.geometry.attributes.position.needsUpdate=true;
   g.pointsGeo.setDrawRange(0,h/3);g.pointsGeo.attributes.position.needsUpdate=true;
   g.material.opacity=opacity*.65;g.pointsMat.opacity=opacity;
  }return active;
 }
 return{root,update,trackCount:selected.length,sourceHistories:families.size};
}

/** Ion glyphs are symbolic; no reaction cross section or nuclear trajectory is calculated. */
export function reactionGlyphs(){
 const root=new T.Group(),sphere=new T.SphereGeometry(1,28,20);
 const colors=['#63c9e4','#ac9ce9','#f6b75d','#ecfaff'];
 const nodes=colors.map(c=>new T.Mesh(sphere,new T.MeshStandardMaterial({color:c,emissive:c,emissiveIntensity:.3,roughness:.27,metalness:.1,transparent:true})));
 root.add(...nodes);const axis=new T.Vector3(.94,.33,.08).normalize();
 function update(t:number,opacity:number){root.visible=opacity>0;const merge=smooth((t-5.9)/.36),out=smooth((t-6.26)/.5);
  nodes[0].position.set(-.42*(1-merge),-.075*(1-merge),0);nodes[1].position.set(.42*(1-merge),.075*(1-merge),0);
  nodes[2].position.copy(axis).multiplyScalar(-out*.22);nodes[3].position.copy(axis).multiplyScalar(out*.88);
  for(let i=0;i<4;i++){const born=i>1?smooth((t-6.22)/.07):1-smooth((t-6.20)/.09);nodes[i].scale.setScalar(i===3?.024:i===2?.057:i===1?.054:.046);nodes[i].material.opacity=opacity*born;nodes[i].visible=born>.001;}
 }
 return {root,update,nodes};
}

/** Lagrangian fluid marker radii integrated in the Euler velocity field; not individual ions. */
export function fluidMarkers(data:Hydro){
 const root=new T.Group(),rings:Array<{line:T.LineLoop;index:number}>=[];
 for(const index of [8,12,16,20,24,30,40,55,75]){
  const geometry=new T.BufferGeometry().setAttribute('position',new T.Float32BufferAttribute(new Float32Array(192*3),3));
  const material=new T.LineBasicMaterial({color:'#d2f0ee',transparent:true,opacity:0,depthWrite:false});
  const line=new T.LineLoop(geometry,material);line.frustumCulled=false;root.add(line);rings.push({line,index});
 }
 function update(time:number,opacity:number){root.visible=opacity>0;const[a,b,u]=bracket(data.snapshots,time);
  for(const {line,index} of rings){const r=blend(a.tracerRadiusM[index],b.tracerRadiusM[index],u),v=line.geometry.attributes.position;
   for(let i=0;i<v.count;i++){const theta=i/v.count*Math.PI*2;v.setXYZ(i,r*Math.cos(theta),r*Math.sin(theta),.000015);}
   v.needsUpdate=true;(line.material as T.LineBasicMaterial).opacity=opacity*.21;
  }
 }
 return{root,update};
}
