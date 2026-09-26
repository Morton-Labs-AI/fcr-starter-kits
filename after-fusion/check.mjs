// SPDX-License-Identifier: MIT OR Apache-2.0
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
const read = name => JSON.parse(readFileSync(new URL(name, import.meta.url), 'utf8'));
const [hydro, neutrons, thermal] = ['hydro', 'neutrons', 'thermal'].map(name => read(`public/data/${name}.json`));
const finite = array => array.every(Number.isFinite);
for (const data of [hydro, thermal]) {
  assert(data.snapshots.length > 100);
  assert(data.snapshots.every((frame, i) => i === 0 || frame.timeS > data.snapshots[i - 1].timeS));
  assert(Math.abs(data.energyResidualRelative) < 1e-9);
}
for (const frame of hydro.snapshots) {
  assert(finite(frame.rhoKgM3) && finite(frame.temperatureK) && finite(frame.velocityMS));
  assert(frame.rhoKgM3.length === 640);
  assert(frame.rhoKgM3.every(value => value > 0) && frame.temperatureK.every(value => value > 0));
}
assert(neutrons.solver === 'OpenMC' && neutrons.version === '0.15.3' && neutrons.histories === 64000);
assert(neutrons.tracks.length === 737 && neutrons.tracks.some(track => track.species === 'photon'));
let primaryCount = 0;
for (const track of neutrons.tracks) {
  assert(track.states.every(state => state.length === 5 && finite(state)));
  assert(track.states.every((state, i) => i === 0 || state[3] >= track.states[i - 1][3]));
  if (track.secondary === 0 && track.species === 'neutron') {
    const [a, b] = track.states;
    assert.deepEqual(a.slice(0, 4), [0, 0, 0, 0]); assert.equal(a[4], 14.1e6);
    const speed = Math.hypot(b[0], b[1], b[2]) / b[3];
    const expected = 299792458 * Math.sqrt(1 - 1 / (1 + a[4] / 939.56542052e6) ** 2);
    assert(Math.abs(speed / expected - 1) < 1e-6); primaryCount++;
  }
}
assert.equal(primaryCount, 192);
const deposition = neutrons.heatingEvPerSource.reduce((a, b) => a + b, 0) * 1.602176634e-19;
assert(Math.abs(thermal.initialEnergyJPerSource / deposition - 1) < 1e-12);
for (const frame of thermal.snapshots) {
  assert(finite(frame.wallDeltaKPerSource) && frame.wallDeltaKPerSource.every(value => value >= 0));
  assert(frame.coolantDeltaKPerSource >= 0);
  assert(Math.abs((frame.remainingEnergyJPerSource + frame.exchangerEnergyJPerSource) / thermal.initialEnergyJPerSource - 1) < 1e-9);
}
const receipt = read('kit-manifest.json');
for (const file of receipt.files.filter(file => file.path.startsWith('public/'))) {
  const bytes = readFileSync(new URL(file.path, import.meta.url));
  assert.equal(bytes.length, file.bytes);
  assert.equal(createHash('sha256').update(bytes).digest('hex'), file.sha256, file.path);
}
console.log('PASS: 3 prepared datasets; 737 tracks; 192 source histories; conservative transport → heat coupling; public asset hashes. No solver executed.');
