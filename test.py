import pandas as pd
import sys
import os
from time import time
from models.essay_scorer import EssayScorer
from models.feedback_generator import QualityFeedback

def test_system():
    print("Starting test system...")
    start_time = time()
    
    # Initialize models
    print("Initializing models...")
    try:
        scorer = EssayScorer()
        feedback_gen = QualityFeedback()
    except Exception as e:
        print(f"Error initializing models: {str(e)}")
        return
    
    # Load data
    print("Loading test essays...")
    try:
        df = pd.read_csv("data/training_set_rel3.tsv", sep='\t', encoding='ISO-8859-1')
        print(f"Loaded {len(df)} essays")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return

    # Test with different essay sets
    print("\nTesting essay scoring across different sets...")
    print("=" * 80)
    
    total_diff = 0
    count = 0
    
    for essay_set in range(1, 9):
        set_essays = df[df['essay_set'] == essay_set].head(2)  # Test 2 essays from each set
        
        print(f"\nEssay Set {essay_set}")
        print("-" * 40)
        
        for _, essay_data in set_essays.iterrows():
            essay_text = essay_data['essay']
            actual_score = essay_data['domain1_score']
            
            # Get normalized actual score
            normalized_actual = scorer.normalize_score(actual_score, essay_set)
            
            print(f"\nEssay excerpt: {essay_text[:100]}...")
            print(f"Original score: {actual_score}")
            print(f"Normalized score (0-10): {normalized_actual:.2f}")
            
            try:
                predicted_score = scorer.predict(essay_text, essay_set)
                diff = abs(predicted_score - normalized_actual)
                total_diff += diff
                count += 1
                
                print(f"Predicted score: {predicted_score:.2f}")
                print(f"Difference: {diff:.2f}")
                
                feedback = feedback_gen.get_feedback(essay_text)
                print("\nFeedback:")
                for category, comments in feedback.items():
                    if comments:
                        print(f"\n{category.title()}:")
                        for comment in comments:
                            print(f"- {comment}")
                            
            except Exception as e:
                print(f"Error processing essay: {str(e)}")
            
            print("-" * 40)
    
    # Print summary
    print("\nTest Summary")
    print("=" * 80)
    print(f"Average score difference: {total_diff/count:.2f}")
    print(f"Tests completed in {time() - start_time:.2f} seconds")
    
    # Save the trained model
    print("\nSaving models...")
    scorer.save_models('saved_models/')

if __name__ == "__main__":
    try:
        test_system()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error occurred: {str(e)}")
        sys.exit(1)
def save_models():
    print("\nSaving models...")
    try:
        scorer = EssayScorer()
        
        # Train models if needed
        print("Training models before saving...")
        df = pd.read_csv("data/training_set_rel3.tsv", sep='\t', encoding='ISO-8859-1')
        
        # Train on first 500 essays
        scorer.train(
            df['essay'].values[:500],
            df['domain1_score'].values[:500],
            df['essay_set'].values[:500]
        )
        
        # Save models
        save_path = 'saved_models/'
        os.makedirs(save_path, exist_ok=True)
        scorer.save_models(save_path)
        print("Models saved successfully!")
        
    except Exception as e:
        print(f"Error saving models: {str(e)}")

if __name__ == "__main__":
    # Your existing test code
    test_system()
    
    # Add this line to save models after testing
    save_models()