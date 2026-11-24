"""Load the legacy saved_models/ artifacts under a modern Python/sklearn/TF stack.

The shipped rf_model.joblib was pickled with scikit-learn 0.24.2. scikit-learn >= 1.3
added a `missing_go_to_left` field to the tree node struct and refuses older node
arrays. We add that field (all zeros: these trees never saw NaNs, so the field is
never read at predict time), which is the same conversion sklearn performs for
compatible versions. Predictions are unchanged.
"""
from __future__ import annotations

import pickle

import numpy as np


def _upgrade_tree_state(state):
    if not isinstance(state, dict):
        return
    nodes = state.get("nodes")
    if not isinstance(nodes, np.ndarray) or nodes.dtype.names is None:
        return
    if "missing_go_to_left" in nodes.dtype.names:
        return
    new_dtype = np.dtype(nodes.dtype.descr + [("missing_go_to_left", "u1")])
    upgraded = np.zeros(nodes.shape, dtype=new_dtype)
    for name in nodes.dtype.names:
        upgraded[name] = nodes[name]
    state["nodes"] = upgraded


def load_legacy_rf(path: str):
    """joblib.load with on-the-fly upgrade of pre-1.3 sklearn tree node arrays."""
    import joblib
    from joblib import numpy_pickle

    unpickler = numpy_pickle.NumpyUnpickler
    key = pickle.BUILD[0]
    original = unpickler.dispatch[key]

    def patched_load_build(self):
        _upgrade_tree_state(self.stack[-1])
        return original(self)

    unpickler.dispatch[key] = patched_load_build
    try:
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = joblib.load(path)
    finally:
        unpickler.dispatch[key] = original
    # Attributes added to trees after 0.24 that predict() may touch.
    for est in getattr(model, "estimators_", []):
        if not hasattr(est, "monotonic_cst"):
            est.monotonic_cst = None
    if not hasattr(model, "monotonic_cst"):
        model.monotonic_cst = None
    return model


def load_legacy_lstm(path: str):
    """The LSTM was saved by TF 2.8 / Keras 2 as HDF5; tf_keras (Keras 2 API) reads it."""
    try:
        import tf_keras

        return tf_keras.models.load_model(path, compile=False)
    except Exception:  # pragma: no cover - fallback
        import keras

        return keras.models.load_model(path, compile=False)


def legacy_rf_predict(model, X) -> np.ndarray:
    """RandomForestRegressor.predict without sklearn's estimator-API checks.

    A regression forest's prediction is the mean of its trees' leaf values, so we read
    the (upgraded) low-level tree structs directly. This sidesteps attributes that
    later sklearn versions expect on the estimator object (e.g. `estimator`).
    """
    X = np.asarray(X, dtype=np.float32)
    preds = [np.asarray(est.tree_.predict(X)).reshape(len(X), -1)[:, 0] for est in model.estimators_]
    return np.mean(preds, axis=0)
