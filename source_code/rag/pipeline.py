"""Retrieval-Augmented Generation pipeline: index -> retrieve -> prompt -> generate."""

import hashlib
import json
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import Settings
from .loaders import list_source_files, load_directory

COLLECTION = "rag_documents"

STRICT_PROMPT = """You are a helpful assistant that answers questions about the documents below \
(for example, a university major handbook).

RULES:
1. Answer ONLY with information found in the CONTEXT. Do not use outside knowledge.
2. If the CONTEXT does not contain the answer, reply exactly: "I couldn't find that in the documents."
3. Cite the page for each fact, like (p. 12).
4. Use bullet points for lists of courses or requirements. Keep course codes exactly as written.
5. Be concise.

CONVERSATION SO FAR:
{history}

CONTEXT:
{context}
---
QUESTION: {question}

ANSWER:"""

# Baseline behaviour from the sample code (kept for comparison experiments)
OPEN_PROMPT = """You are a helpful AI assistant that answers questions based on provided documents.

CONVERSATION SO FAR:
{history}

CONTEXT FROM DOCUMENTS:
{context}
---
QUESTION: {question}

INSTRUCTIONS:
1. If the context contains relevant information, answer based on that.
2. If the context is insufficient, use your general knowledge.
3. Be concise - 2-4 sentences unless more detail is needed.

ANSWER:"""


CONDENSE_PROMPT = """Rewrite the follow-up question so it can be understood without the conversation.
Words like "it", "they", "those", "these", "that course", "the second one" or "them" refer to
something in the conversation: replace them with what they refer to.
Only if the question contains no such reference, return it unchanged. Output only the question.

Examples:
Conversation: User asked about the advanced courses for CS students.
Follow-up: Which of those are about AI?
Standalone: Which of the advanced CS courses are about AI?

Conversation: User asked about the prerequisites for Data Structures & Algorithms.
Follow-up: How many credits is it?
Standalone: How many credits is Data Structures & Algorithms?

CONVERSATION:
{history}

FOLLOW-UP QUESTION: {question}

STANDALONE QUESTION:"""


class PrefixedEmbeddings(Embeddings):
    """nomic-embed-text expects 'search_document: ' / 'search_query: ' prefixes."""

    def __init__(self, inner: Embeddings, doc_prefix: str = "", query_prefix: str = ""):
        self.inner, self.doc_prefix, self.query_prefix = inner, doc_prefix, query_prefix

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.inner.embed_documents([self.doc_prefix + t for t in texts])

    def embed_query(self, text: str) -> List[float]:
        return self.inner.embed_query(self.query_prefix + text)


def list_ollama_models(ollama_url: str) -> List[str]:
    """Names of models pulled into the Ollama server (empty list if unreachable)."""
    try:
        with urllib.request.urlopen(ollama_url.rstrip("/") + "/api/tags", timeout=3) as r:
            return sorted(m["name"] for m in json.load(r).get("models", []))
    except Exception:
        return []


@dataclass
class Source:
    source: str
    page: int
    score: float
    content: str

    @property
    def label(self) -> str:
        return f"{self.source} p.{self.page}" if self.page else self.source


@dataclass
class Prepared:
    question: str
    prompt: str
    sources: List[Source]
    low_confidence: bool
    retrieval_seconds: float = 0.0
    search_query: str = ""          # question actually used for retrieval (after rewriting)


@dataclass
class Answer:
    question: str
    answer: str
    sources: List[Source]
    low_confidence: bool
    model: str
    retrieval_seconds: float
    generation_seconds: float
    extra: Dict = field(default_factory=dict)


class RAGPipeline:
    def __init__(self, settings: Optional[Settings] = None, rebuild: bool = False, verbose: bool = True):
        self.s = settings or Settings()
        self.verbose = verbose
        base = OllamaEmbeddings(model=self.s.embed_model, base_url=self.s.ollama_url)
        if self.s.use_task_prefixes and "nomic" in self.s.embed_model:
            self.embeddings: Embeddings = PrefixedEmbeddings(base, "search_document: ", "search_query: ")
        else:
            self.embeddings = base
        self.db = self._load_or_build(rebuild)
        self._llms: Dict[tuple, OllamaLLM] = {}

    # ------------------------------------------------------------------ indexing
    def _log(self, msg: str):
        if self.verbose:
            print(msg)

    def index_dir(self) -> Path:
        """Index folder name depends on the files AND the settings that affect the vectors,
        so changing chunk size or embedding model never silently reuses a stale index
        (the baseline reused any existing vector_store folder)."""
        files = list_source_files(self.s.data_dir)
        key = json.dumps({
            "files": [(f.name, f.stat().st_size) for f in files],
            "embed": self.s.embed_model,
            "chunk": [self.s.chunk_size, self.s.chunk_overlap],
            "prefix": self.s.use_task_prefixes,
        }, sort_keys=True)
        digest = hashlib.sha1(key.encode()).hexdigest()[:10]
        return self.s.index_root / f"{self.s.data_dir.name}-{digest}"

    def _chroma(self, path: Path) -> Chroma:
        return Chroma(
            collection_name=COLLECTION,
            embedding_function=self.embeddings,
            persist_directory=str(path),
            collection_metadata={"hnsw:space": "cosine"},
        )

    def _load_or_build(self, rebuild: bool) -> Chroma:
        if not self.s.data_dir.exists():
            raise FileNotFoundError(f"Data folder not found: {self.s.data_dir}")
        path = self.index_dir()
        db = self._chroma(path)
        count = db._collection.count()
        if count and not rebuild:
            self._log(f"Loaded existing index {path.name} ({count} chunks)")
            return db
        if count:
            db.delete_collection()
            db = self._chroma(path)

        self._log(f"Indexing documents in {self.s.data_dir} ...")
        documents = load_directory(self.s.data_dir, verbose=self.verbose)
        if not documents:
            raise RuntimeError(f"No .pdf or .txt files with text found in {self.s.data_dir}")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.s.chunk_size,
            chunk_overlap=self.s.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_documents(documents)
        for i, c in enumerate(chunks):
            c.metadata["chunk_id"] = i
        self._log(f"  Embedding {len(chunks)} chunks with {self.s.embed_model} ...")
        t0 = time.perf_counter()
        db.add_documents(chunks)
        self._log(f"  Done in {time.perf_counter() - t0:.1f}s -> {path}")
        return db

    def stats(self) -> Dict:
        return {
            "index": self.index_dir().name,
            "chunks": self.db._collection.count(),
            "files": [f.name for f in list_source_files(self.s.data_dir)],
        }

    # ----------------------------------------------------------------- answering
    def llm(self, model: Optional[str] = None, temperature: Optional[float] = None) -> OllamaLLM:
        model = model or self.s.llm_model
        temperature = self.s.temperature if temperature is None else temperature
        key = (model, temperature)
        if key not in self._llms:
            self._llms[key] = OllamaLLM(
                model=model, base_url=self.s.ollama_url,
                temperature=temperature, num_ctx=self.s.num_ctx, num_predict=self.s.max_tokens,
                client_kwargs={"timeout": 120},   # fail with an error instead of hanging forever
            )
        return self._llms[key]

    def warm_up(self, model: Optional[str] = None) -> None:
        """Load the LLM into (GPU) memory now, so the first real question isn't slow."""
        try:
            self.llm(model).invoke("Reply with OK.")
        except Exception as e:  # warm-up is best effort
            self._log(f"  (warm-up skipped: {e})")

    def retrieve(self, question: str, top_k: Optional[int] = None) -> List[Source]:
        results = self.db.similarity_search_with_score(question, k=top_k or self.s.top_k)
        return [
            Source(
                source=str(doc.metadata.get("source", "unknown")),
                page=int(doc.metadata.get("page", 0) or 0),
                score=round(1.0 - float(dist), 4),   # cosine distance -> similarity
                content=doc.page_content,
            )
            for doc, dist in results
        ]

    @staticmethod
    def _format_history(history: Optional[List[Dict]], turns: int) -> str:
        if not history or turns <= 0:
            return "(none)"
        recent = history[-2 * turns:]
        lines = []
        for m in recent:
            who = "User" if m["role"] == "user" else "Assistant"
            lines.append(f"{who}: {m['content'][:600]}")
        return "\n".join(lines)

    def condense(self, question: str, history: Optional[List[Dict]], model: Optional[str] = None) -> str:
        """Turn a follow-up into a standalone question so retrieval can find the right chunks."""
        if not history or not self.s.rewrite_followups:
            return question
        prompt = (CONDENSE_PROMPT
                  .replace("{history}", self._format_history(history, self.s.history_turns))
                  .replace("{question}", question))
        rewritten = self.llm(model, 0.0).invoke(prompt).strip().strip('"').splitlines()
        return rewritten[0].strip() if rewritten and rewritten[0].strip() else question

    def prepare(self, question: str, history: Optional[List[Dict]] = None,
                top_k: Optional[int] = None, prompt_mode: Optional[str] = None,
                model: Optional[str] = None) -> Prepared:
        t0 = time.perf_counter()
        search_query = self.condense(question, history, model)
        sources = self.retrieve(search_query, top_k)
        elapsed = time.perf_counter() - t0
        best = max((s.score for s in sources), default=0.0)
        low_conf = best < self.s.min_score

        context = "\n\n---\n\n".join(f"[{s.label}]\n{s.content}" for s in sources) or "(no documents)"
        mode = prompt_mode or self.s.prompt_mode
        template = STRICT_PROMPT if mode == "strict" else OPEN_PROMPT
        prompt = (template
                  .replace("{history}", self._format_history(history, self.s.history_turns))
                  .replace("{context}", context)
                  .replace("{question}", search_query))   # the standalone version, so "those" is resolved
        return Prepared(question, prompt, sources, low_conf, elapsed, search_query)

    def stream(self, prepared: Prepared, model: Optional[str] = None,
               temperature: Optional[float] = None) -> Iterator[str]:
        yield from self.llm(model, temperature).stream(prepared.prompt)

    def ask(self, question: str, history: Optional[List[Dict]] = None, model: Optional[str] = None,
            top_k: Optional[int] = None, temperature: Optional[float] = None,
            prompt_mode: Optional[str] = None) -> Answer:
        prepared = self.prepare(question, history, top_k, prompt_mode, model)
        t0 = time.perf_counter()
        text = self.llm(model, temperature).invoke(prepared.prompt).strip()
        return Answer(
            question=question, answer=text, sources=prepared.sources,
            low_confidence=prepared.low_confidence, model=model or self.s.llm_model,
            retrieval_seconds=prepared.retrieval_seconds,
            generation_seconds=time.perf_counter() - t0,
            extra={"search_query": prepared.search_query},
        )
