"""No essay may see its own score: splits are disjoint, conformal calibrates on data the
model never trained on, and the similar-essay index never returns the query essay."""
import os

import numpy as np
import pandas as pd
import pytest

from grader.data import load_asap, load_splits, make_splits
from grader.neighbors import NeighborIndex

ART = "artifacts/grader.joblib"


@pytest.fixture(scope="module")
def splits():
    return load_splits()


def test_every_essay_in_exactly_one_split(splits):
    df = load_asap()
    assert splits.essay_id.is_unique
    assert set(splits.essay_id) == set(df.essay_id)
    assert set(splits.split) == {"train", "val", "calib", "test"}


def test_split_is_reproducible_from_seed(splits):
    again = make_splits(load_asap())
    pd.testing.assert_frame_equal(
        again.sort_values("essay_id").reset_index(drop=True),
        splits.sort_values("essay_id").reset_index(drop=True)[again.columns], check_dtype=False)


def test_index_excludes_self():
    rng = np.random.default_rng(0)
    vecs = rng.normal(size=(20, 8))
    ids = np.arange(100, 120)
    idx = NeighborIndex().add_set(1, ids, rng.integers(2, 13, 20), vecs, ["x"] * 20)
    # querying a training essay with itself: without exclusion it is its own top hit ...
    top, sims = idx.query(1, vecs[5], k=3)
    assert idx.sets[1].ids[top[0, 0]] == 105 and sims[0, 0] == pytest.approx(1.0, abs=1e-5)
    # ... with exclude_id it never appears
    nb = idx.neighbors(1, vecs[5], k=3, exclude_id=105)
    assert 105 not in [n["essay_id"] for n in nb]
    top, _ = idx.query(1, vecs, k=3, exclude_ids=list(ids))
    assert not (idx.sets[1].ids[top] == ids[:, None]).any()


@pytest.mark.skipif(not os.path.exists(ART), reason="run scripts/train_grader.py")
def test_artifact_index_holds_only_training_essays(splits):
    import joblib

    art = joblib.load(ART)
    train_ids = set(splits.loc[splits.split == "train", "essay_id"])
    for s, si in art.index.sets.items():
        assert set(si.ids.tolist()) <= train_ids, f"set {s} index contains non-training essays"


@pytest.mark.skipif(not os.path.exists(ART), reason="run scripts/train_grader.py")
def test_conformal_calibration_size_matches_calib_split(splits):
    import joblib

    art = joblib.load(ART)
    for s, n in art.conformal.n_calib.items():
        assert n == int(((splits.essay_set == s) & (splits.split == "calib")).sum())


@pytest.mark.skipif(not os.path.exists(ART), reason="run scripts/train_grader.py")
def test_graded_essay_never_retrieves_itself(splits):
    """Grade real training essays through the service: their own id must not come back."""
    import joblib

    from grader.service import Grader

    art = joblib.load(ART)
    g = Grader(art)
    s = 3
    si = art.index.sets[s]
    for j in range(5):
        res = g.grade("unused", s, emb=si.vecs[j], style=np.zeros((1, len(art.style_columns))),
                      kev=None, exclude_id=int(si.ids[j]))
        assert int(si.ids[j]) not in [n["essay_id"] for n in res["similar_essays"]]
