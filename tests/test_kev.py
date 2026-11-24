from grader.kev import KevCache, KevClient, request_body, request_key, summarize


def _answer(score, probs):
    return {"type": "score", "score": score, "confidence": 0.5,
            "legend": {str(i): "x" for i in range(len(probs))},
            "probabilities": {str(i): p for i, p in enumerate(probs)}}


def test_request_body_matches_kev_api():
    b = request_body("My essay.", 7)
    assert b["state"] == "My essay." and b["model"] == "kev-latest"
    assert set(b["questions"]) == {"ideas", "organization", "style", "conventions"}
    assert all(q["type"] == "score" for q in b["questions"].values())


def test_summarize_set7_maps_to_rater_scale_and_domain1():
    ans = {t: _answer(2.0, [0.0, 0.1, 0.8, 0.1]) for t in ("ideas", "organization", "style", "conventions")}
    out = summarize(7, ans)
    assert out["traits"]["ideas"]["score"] == 2.0           # set 7 traits are 0-3
    assert set(out["traits"]["ideas"]["probabilities"]) == {"0", "1", "2", "3"}
    assert out["domain1"] == 16.0                            # 2 raters * (2+2+2+2)


def test_summarize_set8_shifts_to_one_based():
    names = ("ideas_and_content", "organization", "voice", "word_choice", "sentence_fluency", "conventions")
    out = summarize(8, {n: _answer(3.0, [0, 0, 0, 1, 0, 0]) for n in names})
    assert out["traits"]["voice"]["score"] == 4.0            # level index 3 -> score 4
    assert out["domain1"] == 2 * (4 * 4) + 2 * 4             # 2(I+O+S+C) + 2C


def test_summarize_holistic_set1():
    out = summarize(1, {"holistic": _answer(3.0, [0, 0, 0, 1, 0, 0])})
    assert out["traits"]["holistic"]["score"] == 4.0          # set 1 rater scale 1-6
    assert out["domain1"] == 8.0                              # two raters summed


def test_client_uses_cache_and_offline(tmp_path):
    path = str(tmp_path / "k.jsonl")
    c = KevClient("http://127.0.0.1:1", cache=KevCache(path))
    assert c.answers("text", 3, offline=True) is None
    c.cache.put(request_key(request_body("text", 3)), {"holistic": _answer(1.0, [0, 1, 0, 0])})
    again = KevClient("http://127.0.0.1:1", cache=KevCache(path))  # reloaded from disk
    assert again.answers("text", 3)["holistic"]["score"] == 1.0
