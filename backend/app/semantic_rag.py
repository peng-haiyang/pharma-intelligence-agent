"""Optional local semantic search with Chroma and sentence-transformer embeddings.

Install requirements-rag.txt to enable. Only local approved .txt/.md files are ingested.
"""
from pathlib import Path
import hashlib
import re

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must be nonnegative and less than chunk_size")
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        chunks.append(normalized[start:end])
        if end == len(normalized):
            break
        start = end - overlap
    return chunks

def read_documents(folder: Path) -> list[dict]:
    """Read curated local documents. No web crawling or implicit downloads."""
    docs = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".txt", ".md"}:
            continue
        if path.is_symlink():
            continue
        relative = path.relative_to(folder).as_posix()
        text = path.read_text(encoding="utf-8")
        for index, chunk in enumerate(chunk_text(text)):
            docs.append({"id": hashlib.sha256(f"{relative}:{index}:{chunk}".encode()).hexdigest(),
                         "text": chunk, "source": relative, "chunk": index})
    return docs

def open_collection(db_path: str, name: str = "japan_pharma"):
    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except ImportError as exc:
        raise RuntimeError("Install backend/requirements-rag.txt to use semantic search") from exc
    client = chromadb.PersistentClient(path=db_path)
    embedding = SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-MiniLM-L12-v2")
    return client.get_or_create_collection(name=name, embedding_function=embedding,
                                           metadata={"hnsw:space": "cosine"})

def ingest(folder: Path, db_path: str) -> int:
    documents = read_documents(folder)
    if not documents:
        return 0
    collection = open_collection(db_path)
    collection.upsert(ids=[d["id"] for d in documents],
                      documents=[d["text"] for d in documents],
                      metadatas=[{"source": d["source"], "chunk": d["chunk"]} for d in documents])
    return len(documents)

def semantic_retrieve(question: str, db_path: str, limit: int = 3) -> list[dict]:
    collection = open_collection(db_path)
    if collection.count() == 0:
        return []
    result = collection.query(query_texts=[question], n_results=min(limit, collection.count()),
                              include=["documents", "metadatas", "distances"])
    return [{"passage": doc, "source": meta["source"], "chunk": meta["chunk"],
             "distance": round(float(distance), 4)}
            for doc, meta, distance in zip(result["documents"][0],
                                           result["metadatas"][0], result["distances"][0])]
