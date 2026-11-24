from grader.style import legacy_clean


def test_legacy_clean_matches_essay_scorer_preprocess():
    import importlib

    from nltk.corpus import stopwords

    es = importlib.import_module("models.essay_scorer")  # imports TensorFlow; slow but exact

    class Fake:
        class feature_extractor:
            stop_words = set(stopwords.words("english"))

    text = "Dear @CAPS1, Computers are GREAT!!! I think they are the best... 100% sure."
    assert legacy_clean(text, Fake.feature_extractor.stop_words) == es.EssayScorer.preprocess_essay(Fake, text)
