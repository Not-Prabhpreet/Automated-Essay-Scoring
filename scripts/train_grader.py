"""Train and evaluate the grader, then write artifacts/grader.joblib for the API.

Data use (fixed split from data/splits.csv):
  train  - fits TF-IDF vocabularies and the ridge heads; the only essays in the
           similar-essay index and in σ(x)
  val    - every choice: ridge alpha per prompt, conformal variant, review threshold
  calib  - only the split-conformal quantiles
  test   - read once at the end for every number reported

Usage: python scripts/train_grader.py
Writes results/step1_model.json, results/step3_conformal.json, results/step3_review.json,
results/step4_neighbors.json, results/speed.json and artifacts/grader.joblib.
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import joblib  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.linear_model import Ridge  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from grader.conformal import SetConformal, coverage, knn_sigma  # noqa: E402
from grader.data import SCORE_RANGES, SETS, clip_round, load_with_splits  # noqa: E402
from grader.features import select_model  # noqa: E402
from grader.metrics import mean_qwk, qwk  # noqa: E402
from grader.neighbors import NeighborIndex  # noqa: E402
from grader.review import PercentileScale, ReviewRule, choose_threshold, flag_stats, is_large_error  # noqa: E402
from grader.service import Grader, GraderArtifact  # noqa: E402
from grader.style import load_style_cache  # noqa: E402

ALPHA = 0.10
REVIEW_BUDGETS = (0.10, 0.20, 0.30)
DEFAULT_BUDGET = 0.20
CONFORMAL_K = (10, 25)
CONFORMAL_BETA = (0.02, 0.05, 0.10)
SPLITS = ("train", "val", "calib", "test")


def r4(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 4)


def main():
    t0 = time.time()
    df = load_with_splits()
    style_df = load_style_cache().set_index("essay_id")
    style_cols = list(style_df.columns)
    style = style_df.loc[df.essay_id].to_numpy(np.float32)
    os.makedirs("results", exist_ok=True)
    os.makedirs("artifacts", exist_ok=True)

    D = {}
    for s in SETS:
        D[s] = {}
        for sp_ in SPLITS:
            m = ((df.essay_set == s) & (df.split == sp_)).to_numpy()
            D[s][sp_] = {"df": df[m].reset_index(drop=True), "texts": df.essay[m].tolist(),
                         "style": style[m], "y": df.domain1_score[m].to_numpy()}

    # ---- step 1: per-prompt models ---------------------------------------------------
    print("step 1: TF-IDF + style ridge per prompt", flush=True)
    models, X, test_q, val_q, style_only, text_only = {}, {}, {}, {}, {}, {}
    for s in SETS:
        tr, va, te = D[s]["train"], D[s]["val"], D[s]["test"]
        m = select_model(s, tr["texts"], tr["style"], tr["y"], va["texts"], va["style"], va["y"])
        models[s] = m
        X[s] = {sp_: m.text_matrix(D[s][sp_]["texts"]) for sp_ in SPLITS}
        val_q[s] = m.val_qwk
        test_q[s] = qwk(te["y"], clip_round(m.predict(X[s]["test"], te["style"]), s))
        # ablations with the same alpha selection on val
        sc = StandardScaler().fit(tr["style"])
        best = max((qwk(va["y"], clip_round(Ridge(alpha=a).fit(sc.transform(tr["style"]), tr["y"]).predict(sc.transform(va["style"])), s)), a)
                   for a in (0.3, 1, 3, 10, 30))
        style_only[s] = qwk(te["y"], clip_round(Ridge(alpha=best[1]).fit(sc.transform(tr["style"]), tr["y"]).predict(sc.transform(te["style"])), s))
        best = max((qwk(va["y"], clip_round(Ridge(alpha=a).fit(X[s]["train"], tr["y"]).predict(X[s]["val"]), s)), a)
                   for a in (0.3, 1, 3, 10))
        text_only[s] = qwk(te["y"], clip_round(Ridge(alpha=best[1]).fit(X[s]["train"], tr["y"]).predict(X[s]["test"]), s))
        print(f"  set {s}: alpha {m.alpha}, val {val_q[s]:.3f}, test {test_q[s]:.3f}", flush=True)
    base = json.load(open("results/baseline.json"))
    step1 = {
        "model": "word (1-2) + char (2-5) TF-IDF + 20 style features -> ridge, one per prompt",
        "selected_by": "val QWK (ridge alpha per prompt)",
        "test_mean": r4(mean_qwk(test_q)), "val_mean": r4(mean_qwk(val_q)),
        "test_per_set": {str(s): r4(test_q[s]) for s in SETS},
        "alpha_per_set": {str(s): models[s].alpha for s in SETS},
        "ablations_test_mean": {
            "original LSTM + RF (baseline)": base["qwk_mean"],
            "style features only (ridge)": r4(mean_qwk(style_only)),
            "TF-IDF only (ridge)": r4(mean_qwk(text_only)),
            "TF-IDF + style (ridge), deployed": r4(mean_qwk(test_q)),
        },
    }
    json.dump(step1, open("results/step1_model.json", "w"), indent=2)
    print(f"  mean test QWK {step1['test_mean']} (baseline {base['qwk_mean']})", flush=True)

    # ---- similar-essay index (train only) ----------------------------------------------
    index = NeighborIndex()
    sims = {}
    for s in SETS:
        sims[s] = {sp_: models[s].similarity_vectors(text_matrix=X[s][sp_]) for sp_ in SPLITS}
        tr = D[s]["train"]
        index.add_set(s, tr["df"].essay_id, tr["y"], sims[s]["train"], tr["texts"])
    preds = {(s, sp_): models[s].predict(X[s][sp_], D[s][sp_]["style"]) for s in SETS for sp_ in ("val", "calib", "test")}

    # ---- step 3a: conformal ------------------------------------------------------------
    print("step 3: conformal ranges", flush=True)
    options = [("plain", None, None)] + [("normalized", k, b) for k in CONFORMAL_K for b in CONFORMAL_BETA]
    results = []
    for kind, k, beta in options:
        cp = SetConformal(alpha=ALPHA, normalized=(kind == "normalized"))
        cov, wid = [], []
        for s in SETS:
            lo_s, hi_s = SCORE_RANGES[s]
            sig = {sp_: (knn_sigma(index.neighbor_scores(s, sims[s][sp_], k), s, beta) if kind == "normalized" else None)
                   for sp_ in ("calib", "val")}
            cp.fit(s, D[s]["calib"]["y"], preds[(s, "calib")], sig["calib"])
            lo, hi = cp.predict(s, preds[(s, "val")], sig["val"])
            cov.append(coverage(D[s]["val"]["y"], lo, hi))
            wid.append(np.mean(hi - lo) / (hi_s - lo_s))
        results.append({"kind": kind, "k": k, "beta": beta, "cp": cp,
                        "val_cov": float(np.mean(cov)), "val_width_unit": float(np.mean(wid))})
        print(f"  {kind:10s} k={k} beta={beta}: val coverage {np.mean(cov):.3f}, width {np.mean(wid):.3f}", flush=True)
    # Deploy an adaptive variant: plain conformal gives every essay of a prompt the same
    # width, so "the range is wide" could not single out an essay for review.
    chosen = min((r for r in results if r["kind"] == "normalized"), key=lambda r: r["val_width_unit"])
    plain = results[0]

    def ranges(r, s, sp_):
        sig = knn_sigma(index.neighbor_scores(s, sims[s][sp_], r["k"]), s, r["beta"]) if r["kind"] == "normalized" else None
        lo, hi = r["cp"].predict(s, preds[(s, sp_)], sig)
        width = 2 * r["cp"].half_width(s, len(lo), sig)
        return lo, hi, width

    per_set, cov_all, w_all, p_cov, p_w = {}, [], [], [], []
    rng_cache = {}
    for s in SETS:
        lo_s, hi_s = SCORE_RANGES[s]
        for sp_ in ("val", "test"):
            rng_cache[(s, sp_)] = ranges(chosen, s, sp_)
        lo, hi, _ = rng_cache[(s, "test")]
        y = D[s]["test"]["y"]
        per_set[str(s)] = {"n_calib": chosen["cp"].n_calib[s], "n_test": int(len(y)), "coverage": r4(coverage(y, lo, hi)),
                           "mean_width_points": r4(np.mean(hi - lo)),
                           "mean_width_frac_of_range": r4(np.mean(hi - lo) / (hi_s - lo_s)), "score_range": [lo_s, hi_s]}
        cov_all.append((y >= lo) & (y <= hi)); w_all.append((hi - lo) / (hi_s - lo_s))
        plo, phi, _ = ranges(plain, s, "test")
        p_cov.append((y >= plo) & (y <= phi)); p_w.append((phi - plo) / (hi_s - lo_s))
    conformal_out = {
        "target_coverage": 1 - ALPHA, "method": "normalized", "k": chosen["k"], "beta": chosen["beta"],
        "test_coverage_overall": r4(np.mean(np.concatenate(cov_all))),
        "test_mean_width_frac_of_range": r4(np.mean(np.concatenate(w_all))),
        "plain_for_comparison": {"test_coverage_overall": r4(np.mean(np.concatenate(p_cov))),
                                 "test_mean_width_frac_of_range": r4(np.mean(np.concatenate(p_w)))},
        "per_set": per_set,
        "options_on_val": [{k: (r4(v) if isinstance(v, float) else v) for k, v in r.items() if k != "cp"} for r in results],
    }
    json.dump(conformal_out, open("results/step3_conformal.json", "w"), indent=2)
    print(f"  test coverage {conformal_out['test_coverage_overall']}, width {conformal_out['test_mean_width_frac_of_range']}", flush=True)

    # ---- step 3b: needs_review -----------------------------------------------------------
    width_scale = PercentileScale()
    stacked = {"val": ([], []), "test": ([], [])}
    for s in SETS:
        width_scale.fit(s, rng_cache[(s, "val")][2])
    for s in SETS:
        for sp_ in ("val", "test"):
            w = width_scale.transform(s, rng_cache[(s, sp_)][2])
            large = is_large_error(D[s][sp_]["y"], clip_round(preds[(s, sp_)], s), s)
            stacked[sp_][0].append(w); stacked[sp_][1].append(large)
    Wv, Lv = np.concatenate(stacked["val"][0]), np.concatenate(stacked["val"][1])
    Wt, Lt = np.concatenate(stacked["test"][0]), np.concatenate(stacked["test"][1])
    review = {"large_error_definition": "|round(pred) - human| >= max(2, 0.2 * score range)",
              "test_large_error_rate": r4(Lt.mean()), "test_large_errors": int(Lt.sum()), "budgets": {}}
    t_default = 1.0
    for budget in REVIEW_BUDGETS:
        tw = choose_threshold(Wv, Lv, budget)
        fv = Wv >= tw if tw < 1 else np.zeros_like(Lv, bool)
        ft = Wt >= tw if tw < 1 else np.zeros_like(Lt, bool)
        review["budgets"][str(budget)] = {"t_width_pct": tw, "val": {k: r4(v) for k, v in flag_stats(fv, Lv).items()},
                                          "test": {k: r4(v) for k, v in flag_stats(ft, Lt).items()}}
        if budget == DEFAULT_BUDGET:
            t_default = tw
        e = review["budgets"][str(budget)]["test"]
        print(f"  budget {budget:.0%}: flag {e['flagged_pct']:.1%}, catch {e['large_errors_caught_pct']:.1%}", flush=True)
    review["deployed_budget"] = DEFAULT_BUDGET
    json.dump(review, open("results/step3_review.json", "w"), indent=2)

    # ---- step 4: neighbours ------------------------------------------------------------
    nb = {}
    for s in SETS:
        te = D[s]["test"]
        top, sim_vals = index.query(s, sims[s]["test"], 3)
        nscores = index.sets[s].scores[top]
        nb[str(s)] = {"mean_top1_similarity": r4(sim_vals[:, 0].mean()),
                      "qwk_mean_of_3_neighbours_vs_human": r4(qwk(te["y"], clip_round(nscores.mean(1), s))),
                      "test_ids_in_index": int(np.isin(te["df"].essay_id, index.sets[s].ids).sum())}
    json.dump(nb, open("results/step4_neighbors.json", "w"), indent=2)

    # ---- artifact ----------------------------------------------------------------------
    art = GraderArtifact(
        config={"alpha": ALPHA, "conformal_k": chosen["k"], "conformal_beta": chosen["beta"],
                "review_budget": DEFAULT_BUDGET, "model_name": "tfidf+style ridge"},
        models=models, conformal=chosen["cp"], index=index,
        review=ReviewRule(t_width=t_default, width_scale=width_scale), style_columns=style_cols,
    )
    joblib.dump(art, "artifacts/grader.joblib", compress=3)

    # ---- speed: full grade() on test essays, style features included -------------------
    g = Grader(art)
    sample = df[df.split == "test"].groupby("essay_set").head(10)
    g.grade(sample.essay.iloc[0], int(sample.essay_set.iloc[0]))  # warm-up
    times = []
    for row in sample.itertuples():
        t = time.perf_counter(); g.grade(row.essay, int(row.essay_set)); times.append(time.perf_counter() - t)
    speed = {"n": len(times), "median_ms": r4(np.median(times) * 1000), "p90_ms": r4(np.percentile(times, 90) * 1000),
             "note": "in-process Grader.grade incl. style features, this machine"}
    json.dump(speed, open("results/speed.json", "w"), indent=2)
    print(f"  grade(): median {speed['median_ms']:.0f} ms, p90 {speed['p90_ms']:.0f} ms", flush=True)
    print(f"done in {time.time() - t0:.0f}s -> artifacts/grader.joblib "
          f"({os.path.getsize('artifacts/grader.joblib') / 2**20:.1f} MB)", flush=True)


if __name__ == "__main__":
    main()
