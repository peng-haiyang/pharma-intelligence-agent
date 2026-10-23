"""Manifest-gated local retrieval. No fetching, uploads, tools, or generated claims."""
from datetime import date
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

from app.semantic_rag import chunk_text

CORPUS = Path(__file__).resolve().parents[2] / 'documents' / 'verified'
MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
HOSTS = {'PMDA': 'www.pmda.go.jp', 'MHLW': 'www.mhlw.go.jp', 'JRS': 'www.jrs.or.jp'}
MAX_BYTES = 100_000


def load_corpus(folder: Path = CORPUS) -> list[dict]:
    """Only reviewed summaries named in the bounded manifest may enter this index."""
    folder = folder.resolve()
    manifest = folder / 'manifest.json'
    if manifest.is_symlink() or manifest.stat().st_size > MAX_BYTES:
        raise ValueError('Unsafe manifest')
    entries = json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(entries, list) or not 0 < len(entries) <= 100:
        raise ValueError('Invalid manifest size')
    docs, seen = [], set()
    for entry in entries:
        required = {'id', 'publisher', 'title', 'url', 'section', 'file', 'language',
                    'published', 'accessed', 'verified', 'verification_method',
                    'content_kind', 'rights', 'sha256'}
        if not isinstance(entry, dict) or set(entry) != required:
            raise ValueError('Invalid provenance fields')
        if any(not isinstance(v, str) or not v.strip() for k, v in entry.items() if k != 'published'):
            raise ValueError('Missing provenance')
        if not re.fullmatch(r'[a-z0-9-]{1,80}', entry['id']) or entry['id'] in seen:
            raise ValueError('Invalid or duplicate document ID')
        seen.add(entry['id'])
        url = urlsplit(entry['url'])
        if (url.scheme != 'https' or url.netloc != HOSTS.get(entry['publisher'])
                or url.path in {'', '/'} or url.fragment):
            raise ValueError('Only direct approved publisher URLs are permitted')
        for field in ('accessed', 'verified', 'published'):
            if entry[field] is not None and date.fromisoformat(entry[field]) > date.today():
                raise ValueError('Future provenance date')
        if date.fromisoformat(entry['verified']) < date.fromisoformat(entry['accessed']):
            raise ValueError('Verification predates access')
        if entry['content_kind'] != 'editorial_summary':
            raise ValueError('Only reviewed editorial summaries are accepted')
        name = entry['file']
        path = folder / name
        if (Path(name).name != name or path.suffix != '.txt' or path.is_symlink()
                or path.resolve().parent != folder or path.stat().st_size > MAX_BYTES):
            raise ValueError('Unsafe source file')
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry['sha256']:
            raise ValueError('Content digest mismatch')
        text = raw.decode('utf-8')
        if not text.strip() or '\x00' in text:
            raise ValueError('Invalid source text')
        for i, passage in enumerate(chunk_text(text)):
            docs.append({**entry, 'chunk': i, 'passage': passage})
    return docs


def collection_name(docs: list[dict]) -> str:
    # Metadata, content, model and chunker version all invalidate old collections.
    digest = hashlib.sha256(json.dumps([MODEL, 'chunks-900-150-v1', docs],
                                      sort_keys=True).encode()).hexdigest()
    return 'verified_' + digest[:40]


def connect(db_path: str):
    from chromadb import PersistentClient
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    return PersistentClient(path=db_path), SentenceTransformerEmbeddingFunction(model_name=MODEL)


def ingest_verified(db_path: str, folder: Path = CORPUS) -> int:
    docs = load_corpus(folder)  # Validate everything before touching the DB/model.
    client, embedding = connect(db_path)
    collection = client.get_or_create_collection(collection_name(docs),
        embedding_function=embedding, metadata={'hnsw:space': 'cosine'})
    collection.upsert(ids=[f"{d['id']}:{d['chunk']}" for d in docs],
        documents=[d['passage'] for d in docs],
        metadatas=[{'document_id': d['id'], 'chunk': d['chunk']} for d in docs])
    return len(docs)


def retrieve_verified(question: str, db_path: str, limit: int = 3,
                      max_distance: float = 0.35) -> list[dict]:
    if not 1 <= limit <= 10 or not 0 <= max_distance <= 2:
        raise ValueError('Invalid retrieval bounds')
    docs = load_corpus()
    client, embedding = connect(db_path)
    # Never silently create an empty or use an obsolete index.
    collection = client.get_collection(collection_name(docs), embedding_function=embedding)
    if collection.count() != len(docs):
        raise ValueError('Incomplete index')
    result = collection.query(query_texts=[question], n_results=min(limit, len(docs)),
                              include=['distances'])
    trusted = {f"{d['id']}:{d['chunk']}": d for d in docs}
    hits = []
    for id, distance in zip(result['ids'][0], result['distances'][0]):
        if id not in trusted or not math.isfinite(distance) or not 0 <= distance <= max_distance:
            continue
        # Resolve evidence from the validated corpus, never DB-supplied text/URLs.
        hits.append({**trusted[id], 'distance': float(distance)})
    return hits
