"""Cache the legacy style features for every ASAP essay (cache/style_features.csv)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grader.data import load_asap  # noqa: E402
from grader.style import build_style_cache  # noqa: E402

if __name__ == "__main__":
    procs = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    out = build_style_cache(load_asap(), processes=procs)
    print("cached", len(out), "essays")
