"""Steps 1, 3, 4: train per-set heads, calibrate conformal ranges, choose review
thresholds, evaluate on test, and write artifacts/grader.joblib for the API.

Data use (fixed split from data/splits.csv):
  train  - fits heads; is the only content of the similar-essay index / sigma(x)
  val    - every choice: head kind/hyper-params/style on-off, conformal variant,
           review thresholds, the percentile scales used by needs_review
  calib  - only the split-conformal quantiles
  test   - read once at the end for every number reported

Kev answers are read from cache/kev_answers.jsonl (scripts/run_kev.py); essays without
a cached answer are treated as "Kev unavailable".

Usage: python scripts/train_grader.py
Writes results/step1_heads.json, results/step3_conformal.json, results/step3_review.json,
results/step4_neighbors.json and artifacts/grader.joblib.
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
from sklearn.ensemble import RandomForestRegressor  # noqa: E402

from grader.conformal import SetConformal, coverage, knn_sigma  # noqa: E402
from grader.data import SCORE_RANGES, SEED, SETS, clip_round  # noqa: E402
from grader.embeddings import get_embedder  # noqa: E402
from grader.heads import select_head  # noqa: E402
from grader.kev import KevCache, KevClient, summarize  # noqa: E402
from grader.metrics import mean_qwk, qwk  # noqa: E402
from grader.neighbors import NeighborIndex  # noqa: E402
from grader.pipeline import by_set_split, load_all  # noqa: E402
from grader.review import (PercentileScale, ReviewRule, choose_thresholds, flag_stats,  # noqa: E402
                           is_large_error)
from grader.service import GraderArtifact, rank_disagreement  # noqa: E402

ALPHA = 0.10
REVIEW_BUDGETS = (0.10, 0.20, 0.30)
DEFAULT_BUDGET = 0.20
CONFORMAL_K = (10, 25)
CONFORMAL_BETA = (0.02, 0.05, 0.10)


def r4(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 4)


def step1(D):
    """Compare head variants. Each (kind, style) variant picks its own per-set
    hyper-parameter on val; the deployed variant is the best by mean val QWK."""
    variants = {}
    for kind in ("ridge", "mlp"):
        for use_style in (False, True):
            name = f"{kind}{'+style' if use_style else ''}"
            heads, val_q, test_q = {}, {}, {}
            for s in SETS:
                tr, va, te = D[s]["train"], D[s]["val"], D[s]["test"]
                h = select_head(s, tr.emb, tr.style, tr.y, va.emb, va.style, va.y, kind, use_style)
                heads[s] = h
                val_q[s] = h.val_qwk
                test_q[s] = qwk(te.y, clip_round(h.predict(te.emb, te.style), s))
            variants[name] = {"heads": heads, "val": val_q, "test": test_q,
                              "params": {s: heads[s].param for s in SETS}}
            print(f"  {name:12s} val {mean_qwk(val_q):.4f}  test {mean_qwk(test_q):.4f}", flush=True)

    # Ablation: style features only, Random Forest retrained per set on our train split
    # (isolates "per-set training on the full train split" from "embeddings").
    rf_val, rf_test = {}, {}
    for s in SETS:
        tr, va, te = D[s]["train"], D[s]["val"], D[s]["test"]
        rf = RandomForestRegressor(n_estimators=300, min_samples_leaf=2, n_jobs=-1, random_state=SEED)
        rf.fit(tr.style, tr.y)
        rf_val[s] = qwk(va.y, clip_round(rf.predict(va.style), s))
        rf_test[s] = qwk(te.y, clip_round(rf.predict(te.style), s))
    print(f"  {'style-RF':12s} val {mean_qwk(rf_val):.4f}  test {mean_qwk(rf_test):.4f}", flush=True)

    best = max(variants, key=lambda n: mean_qwk(variants[n]["val"]))
    table = {
        n: {"val_mean": r4(mean_qwk(v["val"])), "test_mean": r4(mean_qwk(v["test"])),
            "test_per_set": {str(s): r4(v["test"][s]) for s in SETS},
            "hyperparams": {str(s): v["params"][s] for s in SETS}}
        for n, v in variants.items()
    }
    table["style-only RF (retrained per set)"] = {
        "val_mean": r4(mean_qwk(rf_val)), "test_mean": r4(mean_qwk(rf_test)),
        "test_per_set": {str(s): r4(rf_test[s]) for s in SETS}}
    return best, variants[best]["heads"], table


def predict_split(heads, D, s, sp):
    d = D[s][sp]
    return heads[s].predict(d.emb, d.style)


def step3_conformal(heads, D, index):
    """Choose plain vs normalised conformal (and k, beta) by mean val width."""
    options = [("plain", None, None)] + [("normalized", k, b) for k in CONFORMAL_K for b in CONFORMAL_BETA]
    results = []
    for kind, k, beta in options:
        cp = SetConformal(alpha=ALPHA, normalized=(kind == "normalized"))
        val_cov, val_w = [], []
        for s in SETS:
            lo_s, hi_s = SCORE_RANGES[s]
            sig = {}
            for sp in ("calib", "val"):
                if kind == "normalized":
                    sig[sp] = knn_sigma(index.neighbor_scores(s, D[s][sp].emb, k), s, beta)
                else:
                    sig[sp] = None
            cp.fit(s, D[s]["calib"].y, predict_split(heads, D, s, "calib"), sig["calib"])
            lo, hi = cp.predict(s, predict_split(heads, D, s, "val"), sig["val"])
            val_cov.append(coverage(D[s]["val"].y, lo, hi))
            val_w.append(np.mean(hi - lo) / (hi_s - lo_s))
        results.append({"kind": kind, "k": k, "beta": beta, "cp": cp,
                         "val_cov": float(np.mean(val_cov)), "val_width_unit": float(np.mean(val_w))})
        print(f"  conformal {kind:10s} k={k} beta={beta}: val coverage {np.mean(val_cov):.3f}, "
              f"width {np.mean(val_w):.3f} of range", flush=True)
    # Deploy an *adaptive* (normalized) variant: plain conformal gives every essay in a
    # set the same width, so "the range is wide" could not single out any essay for
    # review. Among adaptive variants, the narrowest on val wins; plain is reported.
    chosen = min((r for r in results if r["kind"] == "normalized"), key=lambda r: r["val_width_unit"])
    return chosen, results


def conformal_ranges(chosen, heads, D, index, s, sp):
    pred = predict_split(heads, D, s, sp)
    sig = None
    if chosen["kind"] == "normalized":
        sig = knn_sigma(index.neighbor_scores(s, D[s][sp].emb, chosen["k"]), s, chosen["beta"])
    lo, hi = chosen["cp"].predict(s, pred, sig)
    return pred, lo, hi, 2 * chosen["cp"].half_width(s, len(pred), sig)


def kev_domain1(client, d, s):
    out = np.full(len(d.df), np.nan)
    for i, row in enumerate(d.df.itertuples()):
        ans = client.answers(row.essay, s, offline=True)
        if ans is not None:
            out[i] = summarize(s, ans)["domain1"]
    return out


def main():
    t0 = time.time()
    backend = os.environ.get("EMBEDDING_BACKEND", "local")
    emb_model = get_embedder(backend).model
    print(f"loading data + embeddings ({backend}: {emb_model}) ...", flush=True)
    df, emb, style = load_all(backend)
    D = by_set_split(df, emb, style)
    os.makedirs("results", exist_ok=True)
    os.makedirs("artifacts", exist_ok=True)

    # ---- step 1 ------------------------------------------------------------------
    print("step 1: per-set heads", flush=True)
    best, heads, table = step1(D)
    print(f"  deployed: {best}", flush=True)
    with open("results/step1_heads.json", "w") as f:
        json.dump({"embedding": f"{backend}:{emb_model}", "selected_by": "mean val QWK",
                   "deployed": best, "variants": table}, f, indent=2)

    # ---- similar-essay index (train only) -----------------------------------------
    index = NeighborIndex()
    for s in SETS:
        tr = D[s]["train"]
        index.add_set(s, tr.df.essay_id, tr.y, tr.emb, tr.df.essay.tolist())

    # ---- step 3a: conformal ---------------------------------------------------------
    print("step 3: conformal", flush=True)
    chosen, conf_opts = step3_conformal(heads, D, index)
    per_set, all_cov, all_w_unit = {}, [], []
    cache = {}
    for s in SETS:
        lo_s, hi_s = SCORE_RANGES[s]
        for sp in ("val", "test"):
            cache[(s, sp)] = conformal_ranges(chosen, heads, D, index, s, sp)
        pred, lo, hi, _ = cache[(s, "test")]
        y = D[s]["test"].y
        cov = coverage(y, lo, hi)
        w = hi - lo
        per_set[str(s)] = {"n_calib": chosen["cp"].n_calib[s], "n_test": int(len(y)),
                           "coverage": r4(cov), "mean_width_points": r4(np.mean(w)),
                           "mean_width_frac_of_range": r4(np.mean(w) / (hi_s - lo_s)),
                           "score_range": [lo_s, hi_s]}
        all_cov.append((y >= lo) & (y <= hi))
        all_w_unit.append(w / (hi_s - lo_s))
    # plain conformal on test, for comparison
    plain = next(r for r in conf_opts if r["kind"] == "plain")
    p_cov, p_w = [], []
    for s in SETS:
        lo_s, hi_s = SCORE_RANGES[s]
        lo, hi = plain["cp"].predict(s, predict_split(heads, D, s, "test"))
        p_cov.append((D[s]["test"].y >= lo) & (D[s]["test"].y <= hi))
        p_w.append((hi - lo) / (hi_s - lo_s))
    conformal_out = {
        "plain_for_comparison": {"test_coverage_overall": r4(np.mean(np.concatenate(p_cov))),
                                 "test_mean_width_frac_of_range": r4(np.mean(np.concatenate(p_w)))},
        "target_coverage": 1 - ALPHA,
        "method": chosen["kind"], "k": chosen["k"], "beta": chosen["beta"],
        "test_coverage_overall": r4(np.mean(np.concatenate(all_cov))),
        "test_mean_width_frac_of_range": r4(np.mean(np.concatenate(all_w_unit))),
        "per_set": per_set,
        "options_on_val": [{k: (r4(v) if isinstance(v, float) else v) for k, v in r.items() if k != "cp"}
                           for r in conf_opts],
    }
    with open("results/step3_conformal.json", "w") as f:
        json.dump(conformal_out, f, indent=2)
    print(f"  test coverage {conformal_out['test_coverage_overall']}, "
          f"width {conformal_out['test_mean_width_frac_of_range']} of range", flush=True)

    # ---- step 3b: needs_review --------------------------------------------------------
    print("step 3: needs_review thresholds", flush=True)
    client = KevClient(cache=KevCache())
    pred_scale, kev_scale, width_scale = PercentileScale(), PercentileScale(), PercentileScale()
    sig = {}  # (set, split) -> dict of arrays
    for s in SETS:
        for sp in ("val", "test"):
            pred, lo, hi, cw = cache[(s, sp)]
            sig[(s, sp)] = {"pred": pred, "width": cw,
                            "kev": kev_domain1(client, D[s][sp], s),
                            "large": is_large_error(D[s][sp].y, clip_round(pred, s), s)}
        v = sig[(s, "val")]
        width_scale.fit(s, v["width"])
        pred_scale.fit(s, v["pred"])
        kv = v["kev"][~np.isnan(v["kev"])]
        kev_scale.fit(s, kv if len(kv) else np.array([0.0]))

    def pct(s, sp):
        x = sig[(s, sp)]
        wp = width_scale.transform(s, x["width"])
        dis = rank_disagreement(pred_scale, kev_scale, s, x["pred"], np.nan_to_num(x["kev"]))
        dis = np.where(np.isnan(x["kev"]), np.nan, dis)
        return wp, dis

    # disagreement percentile is relative to val disagreements
    dis_scale = PercentileScale()
    for s in SETS:
        _, dv = pct(s, "val")
        dv = dv[~np.isnan(dv)]
        dis_scale.fit(s, dv if len(dv) else np.array([1.0]))

    def stacked(sp):
        W, K, L, has_kev = [], [], [], []
        for s in SETS:
            wp, dis = pct(s, sp)
            kp = np.where(np.isnan(dis), -1.0, dis_scale.transform(s, np.nan_to_num(dis)))
            W.append(wp); K.append(kp); L.append(sig[(s, sp)]["large"]); has_kev.append(~np.isnan(dis))
        return np.concatenate(W), np.concatenate(K), np.concatenate(L), np.concatenate(has_kev)

    Wv, Kv, Lv, Hv = stacked("val")
    Wt, Kt, Lt, Ht = stacked("test")
    kev_coverage = {"val": r4(Hv.mean()), "test": r4(Ht.mean())}
    review = {"large_error_definition": "|round(pred) - human| >= max(2, 0.2 * score range)",
              "kev_answers_available": kev_coverage,
              "test_large_error_rate": r4(Lt.mean()), "budgets": {}}
    rules = {}
    for budget in REVIEW_BUDGETS:
        entry = {}
        for name, use_kev in (("width_only", False), ("width_or_kev", True), ("kev_only", True)):
            wv = Wv if name != "kev_only" else np.zeros_like(Wv) - 1
            tw, tk, _ = choose_thresholds(wv, Kv if use_kev else None, Lv, budget, use_kev)
            if name == "kev_only":
                tw = 1.0
            ft = (Wt >= tw if tw < 1 else np.zeros_like(Lt, bool)) | (Kt >= tk if tk < 1 else np.zeros_like(Lt, bool))
            fv = (Wv >= tw if tw < 1 else np.zeros_like(Lv, bool)) | (Kv >= tk if tk < 1 else np.zeros_like(Lv, bool))
            entry[name] = {"t_width_pct": tw, "t_kev_pct": tk,
                           "val": {k: r4(v) for k, v in flag_stats(fv, Lv).items()},
                           "test": {k: r4(v) for k, v in flag_stats(ft, Lt).items()}}
            if budget == DEFAULT_BUDGET:
                rules[name] = (tw, tk)
        review["budgets"][str(budget)] = entry
        print(f"  budget {budget:.0%}: " + "; ".join(
            f"{n}: flag {e['test']['flagged_pct']:.1%} catch {e['test']['large_errors_caught_pct']:.1%}"
            for n, e in entry.items()), flush=True)
    review["deployed_budget"] = DEFAULT_BUDGET
    with open("results/step3_review.json", "w") as f:
        json.dump(review, f, indent=2)

    # ---- step 4: neighbours --------------------------------------------------------
    nb = {}
    for s in SETS:
        te = D[s]["test"]
        top3 = index.neighbor_scores(s, te.emb, 3)
        top, sims = index.query(s, te.emb, 3)
        nb[str(s)] = {"mean_top1_similarity": r4(sims[:, 0].mean()),
                      "qwk_mean_of_3_neighbours_vs_human": r4(qwk(te.y, clip_round(top3.mean(1), s))),
                      "test_ids_in_index": int(np.isin(te.df.essay_id, index.sets[s].ids).sum())}
    with open("results/step4_neighbors.json", "w") as f:
        json.dump(nb, f, indent=2)

    # ---- artifact ------------------------------------------------------------------
    def make_rule(tw, tk):
        r = ReviewRule(t_width=tw, t_kev=tk, width_scale=width_scale, kev_scale=dis_scale)
        return r

    art = GraderArtifact(
        config={"embedding_backend": backend, "embedding_model": emb_model,
                "head": best, "use_style": "+style" in best, "alpha": ALPHA,
                "conformal_method": chosen["kind"], "conformal_k": chosen["k"] or 10,
                "conformal_beta": chosen["beta"] or 0.0, "review_budget": DEFAULT_BUDGET,
                "model_name": f"{best} on {emb_model}"},
        heads=heads, conformal=chosen["cp"], index=index,
        rule_with_kev=make_rule(*rules["width_or_kev"]),
        rule_without_kev=make_rule(*rules["width_only"]),
        pred_scale=pred_scale, kev_scale=kev_scale,
        style_columns=list(style.columns),
    )
    # the review rule compares percentiles of *disagreement*, so the kev scale it
    # needs is dis_scale; rank_disagreement itself needs the Kev score CDF
    art.rule_with_kev.kev_scale = dis_scale
    joblib.dump(art, "artifacts/grader.joblib", compress=3)
    print(f"done in {time.time() - t0:.0f}s -> artifacts/grader.joblib", flush=True)


if __name__ == "__main__":
    main()
