# BEAVRS: from benchmark source to inspectable data

**Evidence: published measurements and a source-model geometry projection.**
This kit reproduces the JSON used to explore a PWR core, assemblies, pins,
power history, boron data, and detector campaigns. No neutronics solver runs.

From this directory, with Python 3.10 or newer:

```sh
python3 tools/project_beavrs.py --check
python3 tools/project_beavrs.py
python3 tools/project_beavrs.py --check
```

The first check compares every derived JSON byte to its pinned source. The
middle command regenerates `public/beavrs/` and a reproduction ZIP. Expected
results include 193 assemblies per cycle, 64 fresh assemblies in cycle 2,
and all bundled detector campaigns. Run `python3 inspect.py` for a compact
summary. Missing or altered source files cause the check to fail.

Try changing a copy of the projection to add an explanation of a geometry
parameter. Keep the source values unchanged. Lengths in the source model are
centimetres; display geometry uses metres, Y-up. Missing measurements remain
missing. Cycle 2 reused assemblies retain their initial enrichment rather
than inventing a depleted composition. Detector uncertainty columns and
normalization are preserved; they are not reinterpreted confidence intervals.

The MIT source subset is pinned at
`1ccae04dc3830a5977f08ed7f5f7e1e51ded0d22` from
https://github.com/mit-crpg/BEAVRS. Original file hashes and upstream links are
in `public/beavrs/manifest.json`; the original license is in
`research/beavrs/source/LICENSE`.

## Advanced: run a transport model

The upstream OpenMC model sources are included for study. To execute them,
follow the pinned upstream model documentation and install OpenMC plus a
compatible cross-section library separately. Set `OPENMC_CROSS_SECTIONS` to
your library's `cross_sections.xml`, record OpenMC/data versions and hashes,
and compare predictions to the benchmark measurements with their declared
normalization. The beginner JSON check does not establish solver readiness,
convergence, or agreement with measurements. This kit does not supply a
cross-section library or promise bitwise Monte Carlo reproduction.

If `--check` reports stale files, rerun projection in a copy and inspect the
diff; do not accept a changed result without understanding its source.
