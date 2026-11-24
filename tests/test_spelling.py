"""The fast spelling check must give exactly the original TextBlob answers."""
import numpy as np
import pandas as pd
import pytest

from grader.data import load_asap
from models.feature_extractor import _misspelled_reference, is_misspelled

TRICKY = ["the", "teh", "recieve", "computers,", "@caps1", "1st", "don't", "...", "Hello",
          "xqzvbn", "u", "lol!!", "co-operate", "3.5", "_", "naïve", "mispelled", "@percent1"]


@pytest.mark.parametrize("word", TRICKY)
def test_matches_reference_on_edge_cases(word):
    assert is_misspelled(word) == _misspelled_reference(word)


def test_matches_reference_on_real_essay_words():
    df = load_asap()
    rng = np.random.default_rng(3)
    essays = df.essay.iloc[rng.choice(len(df), 8, replace=False)]
    words = [w for e in essays for w in e.lower().split() if len(w) > 2]
    assert [is_misspelled(w) for w in words] == [_misspelled_reference(w) for w in words]


def test_matches_cached_original_features():
    """cache/style_features.csv was built with the original per-word correct()."""
    import os

    if not os.path.exists("cache/style_features.csv"):
        pytest.skip("run scripts/build_style_features.py")
    from grader.style import style_features

    cache = pd.read_csv("cache/style_features.csv").set_index("essay_id")
    df = load_asap().set_index("essay_id")
    ids = cache.sample(40, random_state=5).index
    fresh = style_features(df.loc[ids, "essay"].tolist())
    assert (fresh.spelling_errors.to_numpy() == cache.loc[ids, "spelling_errors"].to_numpy()).all()
