FROM python:3.8-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

# First install protobuf and tensorflow with specific versions
RUN pip install --no-cache-dir \
    protobuf==3.20.0 \
    tensorflow==2.8.0

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download models after all dependencies are installed
RUN python -m spacy download en_core_web_sm
# Add stopwords to the NLTK download command
RUN python -m nltk.downloader punkt averaged_perceptron_tagger wordnet stopwords

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]