# Automated Essay Scoring System

A full-stack application that uses deep learning and machine learning techniques to automatically score essays and provide detailed feedback. The system combines LSTM neural networks and Random Forest models to provide accurate scoring, along with detailed feedback on various aspects of writing quality.

<img width="700" alt="image" src="https://github.com/user-attachments/assets/6f023f39-03e1-4ed2-b9e7-f6ed58b770cc" />
</br>
<img width="700" alt="image" src="https://github.com/user-attachments/assets/ed6b3d27-3b78-4e29-baf8-42de4a82f161" />
</br>
<img width="731" alt="image" src="https://github.com/user-attachments/assets/607da646-acc3-4362-8bb2-f85b27681095" />
</br>
<img width="926" alt="image" src="https://github.com/user-attachments/assets/448607aa-b521-4bd3-a6bd-8898b7c2c829" />





## Features

- **Intelligent Essay Scoring**: Uses a hybrid model combining LSTM and Random Forest for accurate scoring
- **Detailed Feedback Generation**: Provides specific feedback on multiple aspects:
  - Readability metrics
  - Grammar and spelling
  - Coherence and structure 
  - Argumentation quality
- **Support for Multiple Essay Types**: Handles 8 different essay sets with customized scoring
- **Modern Web Interface**: Responsive React frontend with Tailwind CSS and GSAP animations
- **RESTful API**: FastAPI backend with comprehensive scoring endpoints

## Architecture

### Backend
- Python 3.8
- FastAPI for API endpoints
- TensorFlow/Keras for LSTM model
- scikit-learn for Random Forest model
- NLTK and spaCy for NLP tasks
- Word2Vec for word embeddings

### Frontend
- React
- Tailwind CSS for styling
- GSAP for animations
- Responsive design

## Installation

### Backend Setup

1. Clone the repository:
<code> git clone https://github.com/yourusername/essay-scorer.git
        cd essay-scorer</code>

2. Using Docker:
<code>docker build -t essay-scorer .</code>
<code>docker run -p 8000:8000 essay-scorer</code>

3. Manual Setup:
<code>
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download required NLTK data
python -m nltk.downloader punkt averaged_perceptron_tagger wordnet stopwords

# Download spaCy model
python -m spacy download en_core_web_sm
</code>

### Frontend Setup:
<code>
cd frontend
npm install
npm run dev
</code>

## API Endpoints:
### Main Endpoints:

-POST /score

  -Score an essay and get feedback
  -Request body: {"essay": "string", "essay_set": integer}
  -Returns score and detailed feedback


-GET /essay-sets

  -Get information about available essay sets
  -Returns descriptions and score ranges for each essay set

## Model Details
### LSTM Model

Three-layer architecture with dropout
Word2Vec embeddings input
Trained on 12,976 essays

### Random Forest Model

### Features include:

Text statistics (word count, sentence length, etc.)
Readability metrics
Grammar and spelling checks
Coherence measures
Argument structure analysis



### Performance Metrics

Random Forest MSE: 0.88
SVR MSE: 2.83
Combined model shows improved performance over individual models

### Docker Support
The project includes a Dockerfile for easy deployment. The container includes:

Python 3.8 slim base
All required dependencies
Pre-downloaded NLTK and spaCy models
Exposed port 8000

## Dependencies
### Backend

tensorflow==2.8.0
fastapi
uvicorn
numpy
pandas
scikit-learn
nltk
spacy
gensim

### Frontend

react
tailwindcss
gsap
axios




