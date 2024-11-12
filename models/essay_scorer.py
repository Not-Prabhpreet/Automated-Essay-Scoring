import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import re
import keras
from gensim.models import KeyedVectors
from nltk.tokenize import word_tokenize
from .feature_extractor import FeatureExtractor


class EssayScorer:
    """Main essay scoring class with multiple models"""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.rf_model = None
        self.lstm_model = None
        self.word2vec_model = None
        self.load_models('saved_models/')

    def normalize_score(self, score, essay_set):
        """Normalize scores to 0-10 scale"""
        # Score ranges for each essay set
        score_ranges = {
            1: (2, 12),    # Essay set 1: 2-12 points
            2: (1, 6),     # Essay set 2: 1-6 points
            3: (0, 3),     # Essay set 3: 0-3 points
            4: (0, 3),     # Essay set 4: 0-3 points
            5: (0, 4),     # Essay set 5: 0-4 points
            6: (0, 4),     # Essay set 6: 0-4 points
            7: (0, 30),    # Essay set 7: 0-30 points
            8: (0, 60)     # Essay set 8: 0-60 points
        }
        
        if essay_set in score_ranges:
            min_score, max_score = score_ranges[essay_set]
            normalized = (score - min_score) / (max_score - min_score) * 10
            return max(0, min(10, normalized))
        return score
        
        
    def preprocess_essay(self, essay):
        """Clean and normalize essay text"""
        # Remove special characters
        essay = re.sub(r'[^A-Za-z\s]', '', essay)
        
        # Convert to lowercase
        essay = essay.lower()
        
        # Simple word splitting
        words = essay.split()
        
        # Remove stopwords
        words = [w for w in words if w not in self.feature_extractor.stop_words]
        
        return ' '.join(words)
    
    def extract_features(self, essays):
        """Extract all features for essays"""
        from tqdm import tqdm
        
        print("Extracting features...")
        batch_size = 100
        all_features = []
        
        # Process essays in batches
        for i in range(0, len(essays), batch_size):
            batch = essays[i:min(i + batch_size, len(essays))]
            print(f"Processing essays {i} to {i+len(batch)}...")
            
            # Preprocess batch
            cleaned_essays = [self.preprocess_essay(essay) for essay in tqdm(batch, desc="Preprocessing")]
            
            # Get features for batch
            features = self.feature_extractor.transform(cleaned_essays)
            all_features.append(features)
        
        # Combine all features
        return pd.concat(all_features) if len(all_features) > 1 else all_features[0]
        
    def train(self, essays, scores, essay_sets=None):
        """Train both traditional ML and deep learning models"""
        print("Training on initial 500 essays...")
        
        if essay_sets is None:
            # Default to essay set 1 if not provided
            essay_sets = [1] * len(essays)
        
        # Normalize scores before training
        print("Normalizing scores...")
        normalized_scores = [
            self.normalize_score(score, essay_set) 
            for score, essay_set in zip(scores[:500], essay_sets[:500])
        ]
        
        # Extract features
        print("Extracting features for training...")
        features = self.extract_features(essays[:500])
        
        # Train Random Forest
        print("Training Random Forest model...")
        self.rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            n_jobs=-1,
            random_state=42
        )
        
        self.rf_model.fit(features, normalized_scores)
        print("Random Forest model trained successfully")
        
        
   
    def predict(self, essay, essay_set=1):
        """Get essay score prediction with dynamic weighting"""
        try:
            # Extract features for Random Forest
            rf_features = self.extract_features([essay])
            
            # Initialize model if needed
            if self.rf_model is None:
                print("Training a new Random Forest model...")
                df = pd.read_csv("data/training_set_rel3.tsv", sep='\t', encoding='ISO-8859-1')
                self.train(
                    df['essay'].values[:500],
                    df['domain1_score'].values[:500],
                    df['essay_set'].values[:500]
                )
            
            # Get RF prediction
            rf_pred = self.rf_model.predict(rf_features)[0]
            
            # Try LSTM prediction
            lstm_pred = None
            if self.lstm_model is not None:
                lstm_features = self.prepare_lstm_features(essay)
                if lstm_features is not None:
                    try:
                        lstm_pred = self.lstm_model.predict(lstm_features)[0][0]
                        print(f"LSTM prediction: {lstm_pred}")
                    except Exception as e:
                        print(f"LSTM prediction failed: {str(e)}")
            
            # Dynamic weighting based on essay set
            if lstm_pred is not None:
                # Higher RF weight for better performing sets
                rf_weight = 0.6 if essay_set in [1, 2, 6] else 0.4
                lstm_weight = 1 - rf_weight
                
                final_pred = (rf_pred * rf_weight + lstm_pred * lstm_weight)
                print(f"Combined prediction (RF: {rf_pred:.2f} * {rf_weight}, LSTM: {lstm_pred:.2f} * {lstm_weight})")
            else:
                final_pred = rf_pred
                print(f"Using only Random Forest prediction: {rf_pred:.2f}")
            
            # Return normalized prediction
            normalized_pred = max(0, min(10, final_pred))  # Ensure prediction is between 0 and 10
            # Return calibrated prediction
            final_pred = self.calibrate_prediction(final_pred, essay_set)
            normalized_pred = max(0, min(10, final_pred))
            return normalized_pred
            
                
        except Exception as e:
            print(f"Error in scoring: {str(e)}")
            return 5.0  # Return middle score as fallback
    def calibrate_prediction(self, raw_pred, essay_set):
        """More granular score calibration"""
        try:
            # Add these conditions at the start of calibrate_prediction
            if essay_set == 4:  # Set with most low-score issues
                if raw_pred > 2:
                    return raw_pred * 0.6  # Stronger reduction for Set 4
                return raw_pred * 0.4

            if essay_set == 7:  # Set with scaling issues
                return raw_pred * 0.9  # General reduction for Set 7
            # Handle very low scores (0-2)
            if raw_pred < 2:
                return raw_pred * 0.5  # Stronger reduction for very low scores
                
            # Handle low scores (2-4)
            elif raw_pred < 4:
                return raw_pred * 0.8
                
            # Handle mid-range scores (4-6)
            elif 4 <= raw_pred <= 6:
                return raw_pred  # Keep as is
                
            # Handle high scores (6-8)
            elif raw_pred < 8:
                return min(10, raw_pred * 1.05)
                
            # Handle very high scores (8-10)
            else:
                return min(10, raw_pred * 1.1)
                
        except Exception as e:
            print(f"Calibration error: {str(e)}")
            return raw_pred
                
    def prepare_lstm_features(self, essay):
        """Prepare features for LSTM model using Word2Vec"""
        try:
            if self.word2vec_model is None:
                raise ValueError("Word2Vec model not loaded")
            
            # Clean essay
            essay = self.preprocess_essay(essay)
            
            # Convert essay to word vectors
            words = essay.split()
            vector_size = 300  # Word2Vec vector size
            essay_vector = np.zeros((1, 1, vector_size))
            word_count = 0
            
            for word in words:
                if word in self.word2vec_model:
                    essay_vector[0][0] += self.word2vec_model[word]
                    word_count += 1
            
            if word_count > 0:
                essay_vector[0][0] /= word_count
            
            return essay_vector
            
        except Exception as e:
            print(f"Error in LSTM feature preparation: {str(e)}")
            return None

    def save_models(self, path):
        """Save trained models"""
        try:
            if self.rf_model:
                import joblib
                joblib.dump(self.rf_model, f'{path}/rf_model.joblib')
                print("Saved Random Forest model")
            
            if self.lstm_model:
                self.lstm_model.save(f'{path}/lstm_model.h5')
                print("Saved LSTM model")
        except Exception as e:
            print(f"Error saving models: {str(e)}")
    
    def load_models(self, path):
        """Load all models from path"""
        try:
            print("Loading Word2Vec model...")
            self.word2vec_model = KeyedVectors.load_word2vec_format(
                f'{path}/word2vecmodel.bin', 
                binary=True
            )
            print("Word2Vec model loaded successfully")
        except Exception as e:
            print(f"Could not load Word2Vec model: {str(e)}")

        try:
            print("Loading Random Forest model...")
            import joblib
            self.rf_model = joblib.load(f'{path}/rf_model.joblib')
            print("Random Forest model loaded successfully")
        except Exception as e:
            print(f"Could not load Random Forest model: {str(e)}")

        try:
            print("Loading LSTM model...")
            self.lstm_model = keras.models.load_model(f'{path}/final_lstm.h5')
            print("LSTM model loaded successfully")
        except Exception as e:
            print(f"Could not load LSTM model: {str(e)}")
