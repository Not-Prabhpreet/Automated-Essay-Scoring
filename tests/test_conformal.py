import json
import os

import numpy as np
import pytest

from grader.conformal import SetConformal, conformal_quantile, coverage, integer_range, knn_sigma
from grader.data import SCORE_RANGES


def test_quantile_is_finite_sample_rank():
    s = np.arange(1, 20)  # n = 19 -> k = ceil(20 * 0.9) = 18
    assert conformal_quantile(s, 0.1) == 18
    assert conformal_quantile(np.arange(5), 0.1) == float("inf")  # n too small for alpha


def test_integer_range_contains_point_and_is_clipped():
    lo, hi = integer_range([3.4, 11.9, 2.0], [1.0, 3.0, 0.0], essay_set=1)  # set 1: 2-12
    assert list(lo) == [3, 9, 2] and list(hi) == [4, 12, 2]
    assert all(l <= round(p) <= h for l, h, p in zip(lo, hi, [3.4, 11.9, 2.0]))


@pytest.mark.parametrize("normalized", [False, True])
def test_marginal_coverage_on_exchangeable_data(normalized):
    """Split conformal must cover >= 1 - alpha on average over random calib/test draws."""
    rng = np.random.default_rng(0)
    essay_set, alpha = 1, 0.1
    covs = []
    for _ in range(300):
        n_cal, n_test = 200, 200
        x = rng.uniform(0, 1, n_cal + n_test)
        noise_sd = 0.3 + 1.5 * x                  # heteroscedastic
        y_cont = 2 + 10 * x + rng.normal(0, noise_sd)
        y = np.clip(np.rint(y_cont), *SCORE_RANGES[essay_set])
        pred = 2 + 10 * x + rng.normal(0, 0.2, len(x))  # imperfect predictor
        sigma = noise_sd + 0.1 if normalized else None
        cp = SetConformal(alpha=alpha, normalized=normalized)
        cp.fit(essay_set, y[:n_cal], pred[:n_cal], None if sigma is None else sigma[:n_cal])
        lo, hi = cp.predict(essay_set, pred[n_cal:], None if sigma is None else sigma[n_cal:])
        covs.append(coverage(y[n_cal:], lo, hi))
    mean_cov = float(np.mean(covs))
    # theory: E[coverage] in [1 - alpha, 1 - alpha + 1/(n+1)]; integer rounding only adds
    assert 0.895 <= mean_cov <= 0.95, mean_cov


def test_normalized_ranges_adapt_width():
    cp = SetConformal(alpha=0.1, normalized=True).fit(1, [5, 6, 7] * 10, [5, 6, 7] * 10, np.ones(30))
    cp.q[1] = 1.0
    lo, hi = cp.predict(1, [6.0, 6.0], [0.5, 3.0])
    assert (hi - lo)[1] > (hi - lo)[0]


def test_knn_sigma_positive():
    s = knn_sigma(np.array([[4, 4, 4], [2, 6, 10]]), 1, 0.05)
    assert s[0] == pytest.approx(0.5) and s[1] > s[0]


@pytest.mark.skipif(not os.path.exists("results/step3_conformal.json"), reason="run scripts/train_grader.py")
def test_reported_test_coverage_near_target():
    r = json.load(open("results/step3_conformal.json"))
    # 1,947 test essays: a valid 90% method lands within a few points of 0.90
    assert 0.87 <= r["test_coverage_overall"] <= 0.95
