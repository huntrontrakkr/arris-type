"""The skeleton check on a core sample: no feature of these drawings is lost
and regained along the weight, in either style (arris.skeleton). The full
check, every letter and figure on four axis lines, is ``python -m
arris.skeleton``; this keeps a dozen glyphs that pass it passing."""
from __future__ import annotations

import pytest

from arris import skeleton

SAMPLE = ['h', 'l', 'g', 'y', 'C', 'j', 'aogonek', 'uni0498', 'uni04A6', 'e', 'o', 'five']
PLACES = [(w, 0, 0) for w in range(100, 901, 100)]


@pytest.mark.parametrize('style', ['upright', 'italic'])
def test_core_sample_keeps_its_features(style):
    results = skeleton.survey(SAMPLE, style, {'g0/w0': PLACES}, procs=1)
    found = {name: skeleton.faults(per['g0/w0'], PLACES) for name, per in results.items()}
    assert {n: f for n, f in found.items() if f} == {}
