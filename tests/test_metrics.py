import numpy as np
import pytest
from sklearn.metrics import cohen_kappa_score

from grader.metrics import mean_qwk, qwk


def test_perfect_agreement_is_one():
    y = [0, 1, 2, 3, 2, 1]
    assert qwk(y, y) == pytest.approx(1.0)


def test_matches_sklearn_on_random_ratings():
    rng = np.random.default_rng(0)
    for _ in range(50):
        a = rng.integers(0, 7, 200)
        b = np.clip(a + rng.integers(-2, 3, 200), 0, 6)
        assert qwk(a, b) == pytest.approx(cohen_kappa_score(a, b, weights="quadratic"), abs=1e-12)


def test_known_value():
    # hand-computed: one adjacent disagreement among 4 items on a 0-2 scale
    a, b = [0, 1, 2, 2], [0, 1, 2, 1]
    assert qwk(a, b) == pytest.approx(cohen_kappa_score(a, b, weights="quadratic"))
    assert 0 < qwk(a, b) < 1


def test_symmetric_and_penalises_distance():
    a = [0, 0, 1, 1, 2, 2, 3, 3]
    near = [0, 1, 1, 2, 2, 3, 3, 3]
    far = [3, 3, 2, 2, 1, 1, 0, 0]
    assert qwk(a, near) == pytest.approx(qwk(near, a))
    assert qwk(a, near) > 0.5 > qwk(a, far)
    assert qwk(a, far) < 0


def test_explicit_rating_range_and_errors():
    assert qwk([1, 2], [1, 2], min_rating=0, max_rating=5) == pytest.approx(1.0)
    with pytest.raises(ValueError):
        qwk([1, 2], [1])
    assert mean_qwk({1: 0.5, 2: 0.7}) == pytest.approx(0.6)
