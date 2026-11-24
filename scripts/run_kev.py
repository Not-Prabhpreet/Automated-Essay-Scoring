"""Step 2 (offline): ask Kev the rubric questions for essays and cache the answers.

Needs a Kev server (see README "Kev rubric feedback"):
    python -m kev.serve --run jaredpalmer/kev-0.8b@v1.0 --device cpu --port 8009

Resumable: answers are appended to cache/kev_answers.jsonl and cached essays are skipped.

Usage: python scripts/run_kev.py --splits test,val --sets 7,8 [--limit N] [--url ...]
"""
import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from grader.data import load_with_splits  # noqa: E402
from grader.kev import DEFAULT_URL, KevCache, KevClient  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", default="test,val")
    ap.add_argument("--sets", default="7,8,1,2,3,4,5,6")
    ap.add_argument("--limit", type=int, default=0, help="max essays per (set, split); 0 = all")
    ap.add_argument("--url", default=DEFAULT_URL)
    args = ap.parse_args()

    df = load_with_splits()
    client = KevClient(args.url, cache=KevCache())
    if not client.is_up():
        sys.exit(f"Kev server not reachable at {args.url}")
    sets = [int(s) for s in args.sets.split(",")]
    splits = args.splits.split(",")
    jobs = []
    for s in sets:
        for sp in splits:
            d = df[(df.essay_set == s) & (df.split == sp)].sort_values("essay_id")
            if args.limit:
                d = d.head(args.limit)
            jobs += [(r.essay, s) for r in d.itertuples()]
    todo = [(e, s) for e, s in jobs if client.answers(e, s, offline=True) is None]
    print(f"{len(jobs)} essays requested, {len(jobs) - len(todo)} cached, {len(todo)} to run", flush=True)
    t0 = time.time()
    for i, (essay, s) in enumerate(todo, 1):
        client.answers(essay, s)
        if i % 10 == 0 or i == len(todo):
            el = time.time() - t0
            print(f"{i}/{len(todo)}  {el / i:.1f}s/essay  eta {(len(todo) - i) * el / i / 60:.0f} min", flush=True)


if __name__ == "__main__":
    main()
