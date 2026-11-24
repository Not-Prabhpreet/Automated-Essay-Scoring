FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.hf \
    USE_TF=0 \
    TOKENIZERS_PARALLELISM=false \
    # PyTorch threads: match the machine's vCPUs (Fly shared-cpu-1x = 1); more threads
    # than CPUs makes every request much slower. Override with -e OMP_NUM_THREADS=N.
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1

WORKDIR /app

# CPU-only PyTorch (the default wheel bundles CUDA and is several GB larger)
RUN pip install --no-cache-dir torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bake model data into the image so startup needs no network
RUN python -m nltk.downloader -q -d /usr/local/share/nltk_data stopwords \
 && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

COPY . .
ENV HF_HUB_OFFLINE=1

EXPOSE 8080
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
