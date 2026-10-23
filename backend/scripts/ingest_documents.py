"""Usage: python scripts/ingest_documents.py --source ../documents/approved --db ../.chroma"""
import argparse
from pathlib import Path
from app.semantic_rag import ingest

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--db", default="../.chroma")
    args = parser.parse_args()
    if not args.source.is_dir():
        parser.error("Source directory does not exist")
    print(f"Ingested {ingest(args.source, args.db)} chunks")
