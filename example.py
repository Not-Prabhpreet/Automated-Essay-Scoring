from models.essay_scorer import EssayScorer
from models.feedback_generator import QualityFeedback

# Initialize scorer and feedback generator
scorer = EssayScorer()
feedback_gen = QualityFeedback()

# Test with a sample essay
essay = "This is a test essay. It contains multiple sentences."
try:
    score = scorer.predict(essay)
    print(f"Essay Score: {score}")
    
    feedback = feedback_gen.get_feedback(essay)
    print("\nFeedback:")
    for category, comments in feedback.items():
        print(f"\n{category.title()}:")
        for comment in comments:
            print(f"- {comment}")
except Exception as e:
    print(f"Error occurred: {str(e)}")