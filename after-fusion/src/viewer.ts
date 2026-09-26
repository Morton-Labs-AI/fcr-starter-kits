// SPDX-License-Identifier: MIT OR Apache-2.0
import * as T from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { plasmaField, thermalShell } from './fields.ts';
import { fluidMarkers, transportTracks } from './particles.ts';
import type { Hydro, Neutrons, Thermal } from './data.ts';

export async function start() {
  const get = async <R,>(name: string): Promise<R> => {
    const response = await fetch(`/data/${name}.json`);
    if (!response.ok) throw new Error(`Prepared ${name} data could not be loaded.`);
    return response.json() as Promise<R>;
  };
  const [hydro, neutrons, thermal] = await Promise.all([
    get<Hydro>('hydro'), get<Neutrons>('neutrons'), get<Thermal>('thermal'),
  ]);
  const host = document.querySelector<HTMLElement>('#viewport')!;
  const stage = document.querySelector<HTMLSelectElement>('#stage')!;
  const time = document.querySelector<HTMLInputElement>('#time')!;
  const play = document.querySelector<HTMLButtonElement>('#play')!;
  const clock = document.querySelector<HTMLOutputElement>('#clock')!;
  const scope = document.querySelector<HTMLElement>('#scope')!;
  const renderer = new T.WebGLRenderer({ antialias: true, logarithmicDepthBuffer: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = T.ACESFilmicToneMapping;
  renderer.domElement.setAttribute('aria-label', 'Prepared model, controlled by the view and time controls above');
  host.replaceChildren(renderer.domElement);
  const scene = new T.Scene();
  scene.background = new T.Color('#10212c');
  scene.add(new T.HemisphereLight('#eff9ff', '#536778', 3));
  const light = new T.DirectionalLight('#ffffff', 4);
  light.position.set(1, 2, 3); scene.add(light);
  const camera = new T.PerspectiveCamera(40, 1, .000001, 500);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = false;
  const gas = plasmaField(hydro), markers = fluidMarkers(hydro);
  gas.mesh.scale.setScalar(.002);
  const tracks = transportTracks(neutrons), shell = thermalShell(thermal);
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const [assembly, capsule] = await Promise.all([
    loader.loadAsync('/target/assembly-cutaway.glb'),
    loader.loadAsync('/target/capsule-fine-cutaway.glb'),
  ]);
  scene.add(gas.mesh, markers.root, tracks.root, shell.root, assembly.scene, capsule.scene);
  let playing = false;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const stop = () => { playing = false; play.textContent = 'Play this stage'; };
  const motion = () => { if (reduced.matches) stop(); play.disabled = reduced.matches || ['target', 'capsule'].includes(stage.value); };
  reduced.addEventListener('change', motion); motion();
  const scopes: Record<string, string> = {
    target: 'NOT A SIMULATION · Reconstructed pre-shot geometry; no implosion or burn calculation.',
    capsule: 'NOT A SIMULATION · Literature-based reconstruction; interfaces and microscopic detail retain the manifest assumptions.',
    plasma: 'Reduced 1D spherical Euler model with radiative cooling. Prescribed cloud; no laser drive, burn, or experimental validation. Rings follow the calculated fluid velocity.',
    transport: 'OpenMC 0.15.3 · 64,000 source histories · Fe/water test sphere. The visible direction-selected subset is not an unbiased flux estimate. Markers are enlarged.',
    thermal: 'Transport deposition → 1D wall conduction → mixed coolant → sink. Wall and coolant temperatures are normalized separately. No CFD or electrical-efficiency prediction.',
  };
  const render = () => {
    const s = stage.value, u = Number(time.value) / 1000;
    const recordedStage = !['target', 'capsule'].includes(s);
    time.disabled = !recordedStage; play.disabled = reduced.matches || !recordedStage;
    const physical = s === 'plasma' ? u * 8e-9 : s === 'transport' ? u * 2e-6 : u * 600;
    assembly.scene.visible = s === 'target'; capsule.scene.visible = s === 'capsule';
    gas.mesh.visible = markers.root.visible = s === 'plasma';
    tracks.root.visible = s === 'transport'; shell.root.visible = s === 'thermal' || s === 'transport';
    scope.textContent = scopes[s];
    if (s === 'plasma') {
      const stats = gas.update(physical, 1, camera.position.clone().divideScalar(.002));
      markers.update(physical, 1);
      clock.textContent = `${(physical * 1e9).toFixed(2)} ns · ${(stats.radiatedJ / hydro.initialEnergyJ * 100).toFixed(3)}% of initial gas energy radiated`;
    } else if (s === 'transport') {
      const active = tracks.update(physical, 1); shell.update(0, 0, .18, .18);
      clock.textContent = `${(physical * 1e9).toFixed(1)} ns · ${active} visible active track heads`;
    } else if (s === 'thermal') {
      const heat = shell.update(physical, 1, .45, 1);
      clock.textContent = `${physical.toFixed(1)} s · ${(heat.removedFraction * 100).toFixed(1)}% of deposited heat transferred to sink`;
    } else clock.textContent = 'Reconstruction · NOT A SIMULATION';
    renderer.render(scene, camera);
  };
  const reset = () => {
    const distance = { target: .035, capsule: .0045, plasma: .0065, transport: 21, thermal: 21 }[stage.value] ?? 21;
    controls.target.set(0, 0, 0); camera.position.set(distance * .16, distance * .12, distance);
    camera.near = distance / 10000; camera.far = distance * 100; camera.updateProjectionMatrix();
    controls.minDistance = distance / 10; controls.maxDistance = distance * 5;
    controls.update(); render();
  };
  const resize = () => {
    const width = Math.max(host.clientWidth, 300), height = Math.min(650, Math.max(320, width * .6));
    renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix(); render();
  };
  controls.addEventListener('change', render);
  stage.addEventListener('change', () => { stop(); time.value = '0'; reset(); });
  time.addEventListener('input', () => { stop(); render(); });
  document.querySelector('#reset')!.addEventListener('click', reset);
  play.addEventListener('click', () => {
    if (playing) { stop(); return; }
    if (reduced.matches) return;
    playing = true; play.textContent = 'Pause';
    if (Number(time.value) >= 1000) time.value = '0';
    const origin = performance.now() - Number(time.value) * 8;
    const step = (now: number) => {
      if (!playing) return;
      time.value = String(Math.min(1000, (now - origin) / 8)); render();
      if (Number(time.value) >= 1000) stop(); else requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });
  new IntersectionObserver(([entry]) => { if (!entry.isIntersecting) stop(); }).observe(host);
  new ResizeObserver(resize).observe(host);
  reset(); resize();
}
