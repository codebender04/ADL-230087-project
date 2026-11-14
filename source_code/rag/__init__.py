"""Local RAG pipeline: PDF/TXT loading, Chroma indexing, Ollama generation."""

from .config import Settings
from .pipeline import RAGPipeline, list_ollama_models

__all__ = ["Settings", "RAGPipeline", "list_ollama_models"]
