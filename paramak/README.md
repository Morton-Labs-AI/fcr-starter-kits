# Paramak: a controlled geometry comparison

**Evidence: checked geometry/calculation. NOT A SIMULATION.** Compare exactly
two accepted educational tokamak cases: elongation 2.0 and 1.8. Materials,
equilibrium, engineering loads, and physical feasibility remain unassessed.

With Python 3.10+ and no additional packages:

```sh
python3 check.py
python3 view.py
```

Open `comparison.html` in a browser. Expected output: 14 recorded checks per
case, 15 pairwise intersection checks per case, six positive-volume components,
and plasma-volume ratio approximately 0.9. The script checks the recorded
comparison against the per-component measurements and bundled source hashes;
it does not rerun the original CAD checks. All numbers are source-derived
educational geometry, not Morton reactor performance.

The model is a 180-degree sector. Baseline X/Y/Z extents are 16.2/8.1/10.2 m;
the edit is 16.2/8.1/9.6 m. The original recipe uses centimetres but writes a
STEP file labeled millimetres: **that raw STEP is one tenth the intended
physical size**. The reproduction tool also exports corrected engineering
STEP in mm and display GLBs in metres, Z-up. A Y-up viewer rotates −90° about
X and applies no extra scale. Default non-adaptive CAD volume differs from
the accepted converged adaptive integration; compare the named methods.

## Advanced: regenerate and review CAD

Use an isolated Python 3.12 environment. The recorded run used Python 3.12.14
on macOS ARM64. `advanced/requirements-recorded.txt` pins the scientific
dependencies; availability on another platform must be checked. The source
snapshot is supplied locally, under its original MIT terms. Its small
`pyproject.toml` is an FCR packaging adapter, not an upstream release.

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r advanced/requirements-recorded.txt
.venv/bin/python -m pip install --no-deps ./advanced/source
.venv/bin/python advanced/reproduce_geometry.py --output output/regenerated
```

This standalone adaptation retains the accepted original generator's volume,
bounds, intersection, contact, STEP round-trip and display checks. It verifies
the recipe/source hashes before execution, writes new evidence, and requires
a fresh output directory. VTK offscreen rendering needs native graphics
support; on headless machines that step may fail. Check the reported failure
before accepting artifacts. The advanced CAD rerun is not part of the
standard-library beginner check and is not claimed to have been repeated for
this packaged release.

Review all new whole/cutaway images and geometry checks. STEP timestamps and
assembly identifiers can change bytes on regeneration. Bind the newly
accepted results to their own hashes; do not overwrite the bundled evidence
or label generated-but-unreviewed results accepted. The source snapshot's
reported upstream revision is
`cd4ecfff4aab9f30c945b45c2bfe91f6636d7219`, not a full upstream checkout.
