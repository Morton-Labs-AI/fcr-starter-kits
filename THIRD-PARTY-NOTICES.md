# Sources and licensing

- **BEAVRS:** MIT Computational Reactor Physics Group,
  https://github.com/mit-crpg/BEAVRS, revision
  `1ccae04dc3830a5977f08ed7f5f7e1e51ded0d22`. The source subset retains its
  original MIT license at `beavrs/research/beavrs/source/LICENSE`. Its recorded
  reactor measurements are benchmark data, not Morton measurements.
- **Paramak:** Fusion Energy and Paramak contributors,
  https://github.com/fusion-energy/paramak, reported snapshot revision
  `cd4ecfff4aab9f30c945b45c2bfe91f6636d7219`. The supplied snapshot is not a
  complete Git checkout. Its MIT notice is retained in `paramak/NOTICE.txt`
  and `paramak/advanced/source/LICENSE`. The original source bytes are pinned
  by hashes in the evidence runtime lock. No upstream endorsement is implied.
- **Three.js:** https://github.com/mrdoob/three, MIT; **Vite:**
  https://github.com/vitejs/vite, MIT; **TypeScript:**
  https://github.com/microsoft/TypeScript, Apache-2.0. These are downloaded by
  npm; their package licenses apply separately.
- **OpenMC:** https://github.com/openmc-dev/openmc, MIT. The prepared
  transport data was produced with OpenMC 0.15.3. Neither the solver binary
  nor nuclear data libraries are distributed in these kits.
- **Reconstructed target:** authored educational meshes, not source CAD.
  `after-fusion/public/target/manifest.json` retains the public literature
  citations and parameter assumptions used in the reconstruction. No
  endorsement, target-specific implosion result, or experimental validation
  is implied.

Original Morton Labs code, visualization adapters, authored meshes and
prepared numerical examples in this distribution are MIT OR Apache-2.0.
Third-party source and data retain their own terms. Preserve this notice and
all bundled license files when redistributing.
