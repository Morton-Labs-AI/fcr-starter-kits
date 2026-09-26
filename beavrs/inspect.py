#!/usr/bin/env python3
"""SPDX-License-Identifier: MIT OR Apache-2.0"""
import json
from pathlib import Path

data = json.loads((Path(__file__).parent / 'public/beavrs/dataset.json').read_text())
for cycle, values in data['cycles'].items():
    print(f"Cycle {cycle}: {len(values['assemblies'])} assemblies; "
          f"{sum(a['fresh'] for a in values['assemblies'])} fresh; "
          f"{len(values['campaigns'])} detector campaigns")
print('Published observations and model geometry; no solver executed.')
