"""Central settings. Every value can be overridden with an environment variable,
which is how the Docker container is configured."""

import os
from dataclasses import dataclass, field
from pathlib import Path

# source_code/ directory
BASE_DIR = Path(__file__).resolve().parent.parent


def _env(name: str, default, cast=str):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    if cast is bool:
        return value.strip().lower() in ("1", "true", "yes", "on")
    return cast(value)


@dataclass
class Settings:
    # Folder with the .pdf / .txt knowledge base
    data_dir: Path = field(default_factory=lambda: Path(
        _env("RAG_DATA_DIR", str(BASE_DIR / "data" / "cs_handbook"))))
    # Root folder for persisted Chroma indexes (one sub-folder per configuration)
    index_root: Path = field(default_factory=lambda: Path(
        _env("RAG_INDEX_DIR", str(BASE_DIR / "vector_store"))))

    ollama_url: str = field(default_factory=lambda: _env("OLLAMA_URL", "http://127.0.0.1:11434"))
    embed_model: str = field(default_factory=lambda: _env("RAG_EMBED_MODEL", "nomic-embed-text"))
    llm_model: str = field(default_factory=lambda: _env("RAG_LLM_MODEL", "qwen2.5:3b"))

    chunk_size: int = field(default_factory=lambda: _env("RAG_CHUNK_SIZE", 1000, int))
    chunk_overlap: int = field(default_factory=lambda: _env("RAG_CHUNK_OVERLAP", 200, int))
    top_k: int = field(default_factory=lambda: _env("RAG_TOP_K", 5, int))
    temperature: float = field(default_factory=lambda: _env("RAG_TEMPERATURE", 0.1, float))
    # Ollama's default context window is small; 5 chunks of 1000 chars plus the
    # prompt can overflow it and get silently truncated.
    num_ctx: int = field(default_factory=lambda: _env("RAG_NUM_CTX", 8192, int))
    # Max tokens per answer. Without a cap, small models (0.5b) can fall into repetition
    # loops and generate 100k+ characters until the context window fills up.
    max_tokens: int = field(default_factory=lambda: _env("RAG_MAX_TOKENS", 1024, int))
    # Below this best-chunk similarity the answer is flagged as low confidence.
    min_score: float = field(default_factory=lambda: _env("RAG_MIN_SCORE", 0.45, float))
    # nomic-embed-text was trained with task prefixes; using them improves retrieval.
    use_task_prefixes: bool = field(default_factory=lambda: _env("RAG_TASK_PREFIXES", True, bool))
    # "strict" = answer only from documents; "open" = baseline behaviour (fall back to model knowledge)
    prompt_mode: str = field(default_factory=lambda: _env("RAG_PROMPT_MODE", "strict"))
    # Number of previous chat turns included in the prompt
    history_turns: int = field(default_factory=lambda: _env("RAG_HISTORY_TURNS", 2, int))
    # Rewrite follow-ups ("what about the second one?") into standalone questions before retrieval
    rewrite_followups: bool = field(default_factory=lambda: _env("RAG_REWRITE_FOLLOWUPS", True, bool))
