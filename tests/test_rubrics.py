import numpy as np
import pytest

from grader.data import load_asap
from grader.rubrics import TRAIT_COLUMNS, TRAITS, questions_for, to_domain1


@pytest.mark.parametrize("s", range(1, 9))
def test_questions_are_valid_score_questions(s):
    qs = questions_for(s)
    assert qs
    for q in qs.values():
        assert q["type"] == "score" and isinstance(q["criteria"], list) and len(q["criteria"]) >= 2
        assert all(isinstance(c, str) and c for c in q["criteria"])


def test_trait_level_counts():
    assert all(len(v) == 4 for v in TRAITS[7].values())  # 0-3
    assert all(len(v) == 6 for v in TRAITS[8].values())  # 1-6


@pytest.mark.parametrize("s", [7, 8])
def test_composite_formula_reproduces_human_scores(s):
    """to_domain1 on the *human* trait scores must give the human resolved score
    (two-rater essays; set 8 rater-3 adjudications use a different rule)."""
    df = load_asap()
    d = df[df.essay_set == s]
    if s == 8:
        d = d[d.rater3_trait1.isna()]
    lo = 0 if s == 7 else 1
    ok = []
    for _, r in d.iterrows():
        # mean of the two raters as a level index (rater1 + rater2 = 2 * mean)
        a = {name: (r[f"rater1_trait{c}"] + r[f"rater2_trait{c}"]) / 2 - lo
             for name, c in TRAIT_COLUMNS[s].items()}
        ok.append(np.isclose(to_domain1(s, a), r.domain1_score))
    assert np.mean(ok) == 1.0
