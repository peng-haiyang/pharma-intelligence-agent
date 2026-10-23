"""Explicit offline-approved corpus ingestion; embedding model may download."""
import argparse
from app.verified_rag import ingest_verified

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    args = parser.parse_args()
    print(f'Ingested {ingest_verified(args.db)} verified chunks')
