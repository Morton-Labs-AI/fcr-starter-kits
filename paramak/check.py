#!/usr/bin/env python3
"""Check the prepared evidence with Python's standard library; no CAD executed.
SPDX-License-Identifier: MIT OR Apache-2.0
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
read = lambda name: json.loads((ROOT / 'evidence' / name).read_text())

def check():
    baseline, variant = [read(name + '-checks.json') for name in ('baseline', 'elongation-1p8')]
    comparison = read('comparison.json')
    assert [baseline['elongation'], variant['elongation']] == [2, 1.8]
    for case in (baseline, variant):
        assert len(case['components']) == 6 and len(case['pairs']) == 15
        assert len(case['checks']) == 14 and all(case['checks'].values())
        assert all(component['volume_m3'] > 0 for component in case['components'])
        assert all(not pair['unintended_overlap'] for pair in case['pairs'])
        assert case['physical_validation'] == 'not_assessed'
    for a, b, change in zip(baseline['components'], variant['components'], comparison['component_volume_changes_m3']):
        assert a['id'] == b['id'] == change['id']
        assert a['volume_m3'] == change['baseline'] and b['volume_m3'] == change['variant']
        assert math.isclose(b['volume_m3'] - a['volume_m3'], change['difference'], abs_tol=1e-12)
    ratio = variant['components'][-1]['volume_m3'] / baseline['components'][-1]['volume_m3']
    assert abs(ratio / .9 - 1) <= comparison['plasma_ratio_relative_tolerance']
    assert ratio == comparison['plasma_volume_ratio']
    assert comparison['edit']['continuous_interval_verified'] is False
    for row in read('environment-lock.json')['source_snapshot']:
        source = ROOT / 'advanced/source' / row['path']
        assert source.is_file(), row['path']
        if row['path'] != 'pyproject.toml':
            assert hashlib.sha256(source.read_bytes()).hexdigest() == row['sha256'], row['path']
    print('PASS: 2 recorded cases; 14 checks each; 15 pairs each; plasma ratio', ratio)
    print('Prepared geometry evidence checked. No CAD or physics solver was executed.')
    return baseline, variant

if __name__ == '__main__':
    check()
