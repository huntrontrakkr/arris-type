"""Moved: the variable-font build is the ``arris.vf`` package.

    uv run python -m arris.vf [italic]

This file stays so the old command still builds."""
from arris.vf.build import main

if __name__ == '__main__':
    raise SystemExit(main())
