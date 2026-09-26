#!/usr/bin/env python3
"""Create an offline, inspectable comparison page. SPDX-License-Identifier: MIT OR Apache-2.0"""
import html
from pathlib import Path
from check import check

root = Path(__file__).resolve().parent
baseline, variant = check()
rows = ''.join('<tr><th>' + html.escape(a['id']) + '</th><td>' +
               f"{a['volume_m3']:.6f}</td><td>{b['volume_m3']:.6f}</td></tr>"
               for a, b in zip(baseline['components'], variant['components']))
page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>FCR · Two Paramak geometry cases</title><style>
body{font:17px/1.6 system-ui;max-width:1000px;margin:3rem auto;padding:0 1.5rem;background:#f8f7f3;color:#243333}
.views{display:grid;grid-template-columns:1fr 1fr;gap:1rem}img{width:100%;height:auto}figure{margin:0}
table{border-collapse:collapse;width:100%}td,th{padding:.5rem;text-align:left;border-bottom:1px solid #ccd1ce}
@media(max-width:600px){.views{grid-template-columns:1fr}}</style>
<h1>One change, two checked geometries</h1><p>Elongation changes from 2.0 to 1.8. These are two discrete accepted cases, not a verified continuous design interval.</p>
<p><strong>NOT A SIMULATION.</strong> Materials, equilibrium, physical feasibility and reactor performance have not been assessed.</p>
<div class="views"><figure><img src="images/baseline.png" alt="Baseline Paramak geometry"><figcaption>Baseline · elongation 2.0</figcaption></figure>
<figure><img src="images/elongation-1p8.png" alt="Edited Paramak geometry"><figcaption>Discrete edit · elongation 1.8</figcaption></figure></div>
<h2>Component volume, cubic metres</h2><table><thead><tr><th>Component</th><th>Baseline</th><th>Edit</th></tr></thead><tbody>''' + rows + '''</tbody></table>
<p>Adaptive Gauss–Kronrod CAD volume measurements. Fourteen recorded geometry/display checks pass for each case. Source geometry uses centimetres; display coordinates use metres, Z-up. See the JSON evidence for tolerances and the corrected STEP unit issue.</p>
<p>Source: Fusion Energy and Paramak contributors · MIT license retained in NOTICE.txt.</p></html>'''
(root / 'comparison.html').write_text(page)
print('Open', root / 'comparison.html', 'in a browser. No server required.')
