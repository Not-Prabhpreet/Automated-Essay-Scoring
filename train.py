import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from models.essay_scorer import EssayScorer
from models.feedback_generator import QualityFeedback

def normalize_scores(scores, essay_set):
    """Normalize scores based on essay set ranges"""
    min_range = [2,1,0,0,0,0,0,0]
    max_range = [12,6,3,3,4,4,30,60]
    
    normalized = (scores - min_range[essay_set-1]) / (max_range[essay_set-1] - min_range[essay_set-1])
    return normalized * 10

def train_models(data_path='data/training_set_rel3.tsv', save_path='saved_models/'):
    """Train and save models"""
    print("Loading data...")
    df = pd.read_csv(data_path, sep='\t', encoding='ISO-8859-1')
    
    # Normalize scores
    df['normalized_score'] = df.apply(
        lambda x: normalize_scores(x['domain1_score'], x['essay_set']), 
        axis=1
    )
    
    # Split data
    essays = df['essay'].values
    scores = df['normalized_score'].values
    X_train, X_test, y_train, y_test = train_test_split(
        essays, scores, test_size=0.2, random_state=42
    )
    
    # Initialize and train scorer
    print("Training models...")
    scorer = EssayScorer()
    scorer.train(X_train, y_train)
    
    # Evaluate
    print("Evaluating models...")
    test_predictions = [scorer.predict(essay) for essay in X_test[:100]]  # Test on first 100 for speed
    mse = np.mean((test_predictions - y_test[:100]) ** 2)
    print(f"Mean Squared Error on test set: {mse:.4f}")
    
    # Save models
    print("Saving models...")
    scorer.save_models(save_path)
    print("Training complete!")
    
    # Test feedback generator
    print("\nTesting feedback generator...")
    feedback_gen = QualityFeedback()
    sample_essay = X_test[0]
    feedback = feedback_gen.get_feedback(sample_essay)
    print("\nSample feedback for test essay:")
    for category, comments in feedback.items():
        print(f"\n{category.title()}:")
        for comment in comments:
            print(f"- {comment}")

if __name__ == "__main__":
    train_models()