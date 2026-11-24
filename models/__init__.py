from .feature_extractor import FeatureExtractor
from .feedback_generator import QualityFeedback


def __getattr__(name):
    # EssayScorer pulls in TensorFlow/Keras; import it only when someone asks for it,
    # so the API (which only needs feedback + the embedding grader) starts without TF.
    if name == "EssayScorer":
        from .essay_scorer import EssayScorer

        return EssayScorer
    raise AttributeError(f"module 'models' has no attribute {name!r}")
