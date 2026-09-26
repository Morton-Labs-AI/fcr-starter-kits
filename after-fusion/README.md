# After fusion: inspect a prepared model chain

**Evidence: recorded executed models plus illustrative target geometry.**
This standalone viewer uses the actual prepared plasma, neutron/photon track,
and thermal datasets from the September 24, 2026 educational example. No
solver runs in the browser. It includes reconstructed target meshes and the
original field/particle rendering modules; its simpler stage controls let
you inspect each process independently.

Use Node 22.12+ and npm. From this directory:

```sh
npm ci
npm run check
npm run dev
```

Open the localhost URL printed by Vite (normally http://127.0.0.1:5173).
Choose **Load the 3D view**, select a stage, and move the model-time slider.
Play is an explicit action, pauses offscreen or when the tab is hidden, and
is disabled under reduced motion. The poster and explanations remain usable
without JavaScript or WebGL. A production bundle is `npm run build`.

`node check.mjs` verifies the data without installing browser dependencies:
737 saved particle tracks, 192 recorded primary histories, the 64,000-history
transport run identity, increasing snapshot time, positive fields, energy
bookkeeping, transport-to-thermal deposition, and distributed asset hashes.
These are data checks, not experimental validation.

## What the three models mean

- **Plasma:** a 640-cell spherical Euler calculation with ideal ionized gas
  and optically thin radiative cooling. Initial conditions prescribe a hot
  cloud; there is no laser drive, target implosion, fusion burn, alpha
  stopping, tabulated EOS, or multidimensional instability.
- **Transport:** OpenMC 0.15.3, isotropic 14.1 MeV point source, 6 m vacuum
  cavity, 20 mm Fe-56 wall and 480 mm water blanket. The displayed subset is
  direction-selected for legibility; deposition uses all 64,000 histories.
  The perforated target context is absent from this unperforated test sphere.
- **Heat:** conservative remapping of integrated transport deposition to 80
  spherical wall cells, mixed water, and an exchanger sink. Values are per
  source neutron. Wall and coolant colors use different normalizations.

The plasma and neutron source have independent energy budgets. Only the
transport deposition → heat response connection is quantitatively coupled.
Sink energy fraction is not electricity efficiency, and neither this kit nor
the target reconstruction predicts a commercial reactor's performance.

## Advanced: recompute the data

Work in a copy; these commands overwrite prepared data and create fresh run
records. `advanced/` contains the original model algorithms with output paths
adapted to this kit. Hydro and thermal require NumPy/SciPy; use the versions
recorded in your new environment and record them alongside new results.

```sh
python3 advanced/hydro.py
python3 advanced/thermal.py
```

To rerun transport separately, install OpenMC **0.15.3** and acquire compatible
continuous-energy neutron, photon, and bound-hydrogen thermal-scattering data.
The exact seven data-file hashes used in the recorded run are listed in
`evidence/neutron-run.json`. Set `OPENMC_CROSS_SECTIONS` to the acquired
library's `cross_sections.xml`, then run `python3 advanced/neutrons.py` and
`python3 advanced/thermal.py`. The original OpenMC commit was
`27e38e894697bb32a1dac7848d2618818b6b8daf`; record your own runtime and data
identity. Docker, a mutable image tag, raw HDF5 evidence archives, and nuclear
libraries are not prerequisites for the prepared-data viewer.

Statistical results and bytes may vary by environment. A fresh result will
fail the distributed hash check until it is reviewed and a new release
manifest is deliberately created. Preserve the old evidence for comparison.

If a browser shows the fallback, check WebGL2 support. If `npm ci` fails,
verify Node's version and network access to npm. If the data check fails,
download a fresh kit before changing expected hashes. Literature citations
and reconstruction assumptions remain in `public/target/manifest.json`.
