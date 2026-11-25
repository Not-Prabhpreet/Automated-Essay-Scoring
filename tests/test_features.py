import numpy as np
import scipy.sparse as sp

from grader.features import SetModel, select_model


def _toy():
    rng = np.random.default_rng(0)
    good = "the argument is clear, specific and well supported with detailed evidence and examples"
    bad = "it is good i think it is good because it good"
    texts, y = [], []
    for i in range(80):
        if i % 2:
            texts.append(f"{good} essay {i}")
            y.append(5)
        else:
            texts.append(f"{bad} essay {i}")
            y.append(1)
    style = rng.normal(size=(80, 20)).astype(np.float32)
    return texts, style, np.array(y)


def test_features_are_sparse_and_similarity_rows_are_unit_length():
    texts, style, y = _toy()
    m = SetModel(1).fit_text(texts)
    X = m.text_matrix(texts)
    assert sp.issparse(X) and X.shape[0] == len(texts)
    S = m.similarity_vectors(text_matrix=X)
    assert S.shape[1] == len(m.word.vocabulary_)
    assert np.allclose(np.sqrt(S.multiply(S).sum(axis=1)).A.ravel(), 1.0, atol=1e-5)


def test_model_learns_and_alpha_is_chosen_on_val():
    texts, style, y = _toy()
    m = select_model(2, texts[:60], style[:60], y[:60], texts[60:], style[60:], y[60:])
    pred = m.predict(m.text_matrix(texts[60:]), style[60:])
    assert np.mean(np.abs(pred - y[60:])) < 1.0
    assert m.alpha in (0.3, 1.0, 3.0, 10.0) and m.val_qwk > 0.8
