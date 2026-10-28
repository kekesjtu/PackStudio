"""Validate this native reference point from the repository environment."""
from pathlib import Path
import sys

point = Path(__file__).resolve().parent
repository = next(p for p in point.parents if (p / "tools/pack_sweep").is_dir())
sys.path.insert(0, str(repository))
from tools.pack_sweep.__main__ import main
raise SystemExit(main(["validate", "--point", str(point)]))
