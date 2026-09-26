import * as T from 'three';
import {bracket,blend,type Hydro,type Thermal} from './data.ts';
export function plasmaField(data:Hydro){
 const pixels=new Float32Array(data.spatialCells*4),texture=new T.DataTexture(pixels,data.spatialCells,1,T.RGBAFormat,T.FloatType);texture.minFilter=texture.magFilter=T.LinearFilter;
 const material=new T.ShaderMaterial({transparent:true,depthWrite:false,depthTest:false,side:T.BackSide,uniforms:{field:{value:texture},opacity:{value:0},eye:{value:new T.Vector3(0,0,1)}},vertexShader:`varying vec3 p; void main(){p=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,fragmentShader:`precision highp float;varying vec3 p;uniform sampler2D field;uniform float opacity;uniform vec3 eye;
 vec3 color(float x){vec3 a=vec3(.03,.13,.22),b=vec3(.12,.60,.75),c=vec3(1.,.23,.07),d=vec3(1.,.87,.42);return x<.25?mix(a,b,x*4.):x<.65?mix(b,c,(x-.25)/.4):mix(c,d,(x-.65)/.35);}
 void main(){vec3 dir=normalize(p-eye);float b=dot(eye,dir),c=dot(eye,eye)-1.,h=b*b-c;if(h<0.)discard;float near=max(0.,-b-sqrt(h)),far=-b+sqrt(h),step=(far-near)/100.;vec4 sum=vec4(0.);for(int i=0;i<100;i++){vec3 q=eye+dir*(near+(float(i)+.5)*step);float r=length(q);vec4 f=texture2D(field,vec2(clamp(r,0.,1.),.5));float density=clamp(f.r,0.,1.);float alpha=(1.-exp(-density*step*12.))*opacity;vec3 col=color(clamp(f.g,0.,1.));sum.rgb+=(1.-sum.a)*alpha*col;sum.a+=(1.-sum.a)*alpha;}gl_FragColor=vec4(sum.rgb/max(sum.a,.0001),sum.a);}`});
 const mesh=new T.Mesh(new T.SphereGeometry(1,48,32),material);mesh.frustumCulled=false;
 function update(time:number,opacity:number,eye:T.Vector3){const[a,b,u]=bracket(data.snapshots,time);for(let i=0;i<data.spatialCells;i++){pixels[4*i]=Math.max(0,Math.log10(1+Math.max(0,blend(a.rhoKgM3[i],b.rhoKgM3[i],u)-.02)*180)/2);pixels[4*i+1]=Math.max(0,(Math.log10(blend(a.temperatureK[i],b.temperatureK[i],u))-4.2)/2.6);pixels[4*i+3]=1;}texture.needsUpdate=true;material.uniforms.opacity.value=opacity;material.uniforms.eye.value.copy(eye);mesh.visible=opacity>0;return {gasEnergyJ:blend(a.gasEnergyJ,b.gasEnergyJ,u),radiatedJ:blend(a.radiatedJ,b.radiatedJ,u)};}
 return{mesh,update};
}
export function thermalShell(data:Thermal){
 const root=new T.Group(),pixels=new Float32Array(data.wallRadiusM.length*4),texture=new T.DataTexture(pixels,data.wallRadiusM.length,1,T.RGBAFormat,T.FloatType);texture.minFilter=texture.magFilter=T.LinearFilter;
 const phase={value:0},coolant={value:0},visibility={value:1};
 const wall=new T.ShaderMaterial({side:T.DoubleSide,transparent:true,uniforms:{field:{value:texture},phase,coolant,visibility},vertexShader:`#include <common>
#include <logdepthbuf_pars_vertex>
varying vec3 p;void main(){p=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);
#include <logdepthbuf_vertex>
}`,fragmentShader:`#include <logdepthbuf_pars_fragment>
varying vec3 p;uniform sampler2D field;uniform float phase;uniform float coolant;uniform float visibility;void main(){
#include <logdepthbuf_fragment>
float r=length(p);float v=r<=6.02001?texture2D(field,vec2(clamp((r-6.)/.02,0.,1.),.5)).r:coolant;vec3 cold=r<=6.02001?vec3(.29,.37,.42):vec3(.025,.15,.22);vec3 hot=mix(vec3(.13,.48,.63),vec3(1.,.30,.065),clamp(v,0.,1.));gl_FragColor=vec4(mix(cold,hot,phase),visibility);}`});
 root.add(new T.Mesh(new T.RingGeometry(6,6.02,192),wall),new T.Mesh(new T.RingGeometry(6.02,6.5,192,4),wall));
 const outerMat=new T.MeshStandardMaterial({color:'#183747',metalness:.38,roughness:.42,side:T.DoubleSide});
 root.add(new T.Mesh(new T.SphereGeometry(6.5,128,64,Math.PI,Math.PI),outerMat));
 function update(time:number,mix:number,contextOpacity=1,reveal=1){visibility.value=reveal;outerMat.transparent=true;outerMat.opacity=contextOpacity*reveal;outerMat.depthWrite=contextOpacity>.999;const[a,b,u]=bracket(data.snapshots,time);for(let i=0;i<data.wallRadiusM.length;i++){pixels[i*4]=blend(a.wallDeltaKPerSource[i],b.wallDeltaKPerSource[i],u)/data.temperatureNormalizationKPerSource;pixels[i*4+3]=1;}texture.needsUpdate=true;phase.value=mix;coolant.value=blend(a.coolantDeltaKPerSource,b.coolantDeltaKPerSource,u)/data.coolantNormalizationKPerSource;outerMat.color.lerpColors(new T.Color('#183747'),new T.Color(.13+.87*coolant.value,.48-.18*coolant.value,.63-.565*coolant.value),mix);outerMat.emissive.copy(outerMat.color);outerMat.emissiveIntensity=mix*.38;return {coolant:coolant.value,removedFraction:blend(a.exchangerEnergyJPerSource,b.exchangerEnergyJPerSource,u)/data.initialEnergyJPerSource};}
 return{root,update};
}
