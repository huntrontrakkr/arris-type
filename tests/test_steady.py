"""The steady check (arris.steady): a counter only shrinks along the weight."""
from arris import steady


def test_italic_k_counter_shrinks(monkeypatch):
    """The italic k's loop: held by area from where its rule engages, its
    counter shrinks every step to Black on the default and heavy grades
    (1.007's grew from Bold to 875 on the heavy grade and fell to a diamond
    at Black)."""
    monkeypatch.setattr(steady, 'LINES', [(0, 0), (100, 100)])
    monkeypatch.setattr(steady, 'STEP', 25)
    rep = steady.scan_drawings(['k'], 'italic', lo=600, procs=1)[0]
    assert not rep.faults, rep.faults


def test_growth_and_jumps_found(monkeypatch):
    """The reading itself: a counter that grows, and one that jumps."""
    import arris.steady as s

    class V:
        composite = False
        coords = (0,)

        def __init__(self, areas):
            self.areas = iter(areas)

        def at(self, loc):
            a = next(self.areas)
            side = a ** 0.5
            outer = [(0, 0, True), (1000, 0, True), (1000, 1000, True), (0, 1000, True)]
            hole = [(100, 100, True), (100, 100 + side, True), (100 + side, 100 + side, True), (100 + side, 100, True)]
            return [outer, hole]

    weights = list(range(100, 901, s.STEP))
    grow = [10000 - 50 * i for i in range(len(weights))]
    grow[40] = grow[39] * 1.05                      # grows 5% at one step
    monkeypatch.setattr(s, 'LINES', [(0, 0)])
    monkeypatch.setattr('arris.topology.Variable', lambda font, name: V(grow))
    font = type('F', (), {'__getitem__': lambda self, k: type('T', (), {'axes': []})()})()
    s._FONT[:] = [font, False]
    rep = s.scan_glyph('x')
    assert any(f.kind == 'grows' and f.weight == weights[40] for f in rep.faults)
