# RAG handbook chatbot - Streamlit app image.
# Build from the repository root:
#   docker build -f docker/Dockerfile -t rag-handbook .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first so this layer is cached between code changes
COPY source_code/requirements.txt .
RUN pip install -r requirements.txt

COPY source_code/ .

# Defaults for the container; override with -e or docker-compose
ENV OLLAMA_URL=http://ollama:11434 \
    RAG_DATA_DIR=/app/data/cs_handbook \
    RAG_INDEX_DIR=/app/vector_store \
    RAG_LLM_MODEL=qwen2.5:3b \
    RAG_EMBED_MODEL=nomic-embed-text

# Run as a non-root user
RUN useradd --create-home appuser && mkdir -p /app/vector_store && chown -R appuser /app
USER appuser

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--browser.gatherUsageStats=false"]
