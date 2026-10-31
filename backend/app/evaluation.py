"""Stage 4A: offline, corpus-pinned retrieval evaluation; no LLM judge."""
import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import time
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from app.verified_rag import load_corpus, collection_name, MODEL, MODEL_REVISION

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = ROOT / 'benchmarks/japan-pharma-v1.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_benchmark(path=BENCHMARK):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    docs = {d['id']: d for d in load_corpus()}
    seen, pairs = set(), {}
    if not data.get('version') or not data.get('cases'):
        raise ValueError('Empty benchmark')
    for c in data['cases']:
        if c['id'] in seen or c['language'] not in ('en', 'ja') or not c['question'].strip():
            raise ValueError('Invalid case identity')
        seen.add(c['id'])
        pairs.setdefault(c['pair_id'], []).append(c)
        if type(c['expected_abstain']) is not bool or c['expected_abstain'] != (not c['expected_ids']):
            raise ValueError('Inconsistent labels')
        if len(c['expected_ids']) != len(set(c['expected_ids'])):
            raise ValueError('Duplicate gold ID')
        for id in c['expected_ids']:
            d = docs[id]
            if c['source_sha256'] != d['sha256'] or c['source_url'] != d['url']:
                raise ValueError('Stale gold provenance')
    for pair in pairs.values():
        if (len(pair) != 2 or {c['language'] for c in pair} != {'en', 'ja'} or
                pair[0]['expected_ids'] != pair[1]['expected_ids'] or
                pair[0]['expected_abstain'] != pair[1]['expected_abstain']):
            raise ValueError('Invalid bilingual pair')
    return data


def percentile(values, p):
    """Nearest-rank percentile, not interpolation."""
    return sorted(values)[max(0, math.ceil(p * len(values)) - 1)] if values else None


def evaluate(cases, search, *, k=3, clock=time.perf_counter):
    if type(k) is not int or not 1 <= k <= 10:
        raise ValueError('Invalid k')
    trusted = {(d['id'], d['chunk']): d for d in load_corpus()}
    rows = []
    for c in cases:
        start = clock()
        error = None
        try:
            result = search(c['question'], k)
            if not isinstance(result, dict) or result.get('status') not in {
                    'retrieved', 'insufficient_evidence', 'unavailable', 'invalid_request'}:
                raise ValueError('Invalid result status')
            citations = result.get('citations', [])
            if not isinstance(citations, list) or any(not isinstance(x, dict) for x in citations):
                raise ValueError('Invalid citations')
            if (result['status'] == 'retrieved') != bool(citations):
                raise ValueError('Inconsistent status')
        except Exception:
            result, citations, error = {'status': 'error'}, [], 'adapter_error'
        elapsed = (clock() - start) * 1000
        if not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError('Invalid timing')
        # Match citation content against trusted local material, not just an allowlisted host.
        valid = []
        for hit in citations:
            id, chunk = hit.get('id'), hit.get('chunk')
            d = trusted.get((id, chunk)) if isinstance(id, str) and type(chunk) is int else None
            valid.append(bool(d and all(hit.get(f) == d[f] for f in
                ('url', 'sha256', 'passage', 'publisher', 'section'))))
        ids = list(dict.fromkeys(h.get('id') for h in citations[:k] if isinstance(h.get('id'), str)))
        gold = set(c['expected_ids'])
        recalled = len(gold.intersection(ids)) / len(gold) if gold else None
        rr = next((1 / (i + 1) for i, id in enumerate(ids) if id in gold), 0) if gold else None
        operational = result['status'] in {'retrieved', 'insufficient_evidence'}
        # Infrastructure failure is not a successful evidence-based abstention.
        abstained = result['status'] == 'insufficient_evidence'
        rows.append(dict(id=c['id'], pair_id=c['pair_id'], language=c['language'],
            category=c['category'], expected_abstain=c['expected_abstain'], status=result['status'],
            error=error, retrieved_ids=ids, recall_at_k=recalled, reciprocal_rank=rr,
            citation_count=len(citations), valid_citations=sum(valid),
            relevant_valid_citations=sum(v and h.get('id') in gold for v,h in zip(valid,citations)),
            abstention_correct=operational and abstained == c['expected_abstain'],
            operational=operational, latency_ms=round(elapsed, 3)))
    def aggregate(items):
        positives = [r for r in items if not r['expected_abstain']]
        negatives = [r for r in items if r['expected_abstain']]
        count = sum(r['citation_count'] for r in items)
        return dict(cases=len(items), answerable_cases=len(positives), abstention_cases=len(negatives),
            recall_at_k=sum(r['recall_at_k'] for r in positives)/len(positives) if positives else None,
            mrr_at_k=sum(r['reciprocal_rank'] for r in positives)/len(positives) if positives else None,
            citation_provenance_precision=sum(r['valid_citations'] for r in items)/count if count else None,
            citation_relevance_precision=sum(r['relevant_valid_citations'] for r in items)/count if count else None,
            abstention_accuracy=sum(r['abstention_correct'] for r in negatives)/len(negatives) if negatives else None,
            answerable_coverage=sum(r['status']=='retrieved' for r in positives)/len(positives) if positives else None,
            operational_rate=sum(r['operational'] for r in items)/len(items) if items else None,
            latency_p50_ms=percentile([r['latency_ms'] for r in items], .5),
            latency_p95_ms=percentile([r['latency_ms'] for r in items], .95))
    pairs = {}
    for row in rows:
        pairs.setdefault(row['pair_id'], []).append(row)
    paired = [p for p in pairs.values() if len(p)==2]
    return dict(k=k, metrics=aggregate(rows), by_language={l:aggregate([r for r in rows if r['language']==l]) for l in ('en','ja')},
        pair_outcome_agreement=sum((p[0]['retrieved_ids'],p[0]['status']) == (p[1]['retrieved_ids'],p[1]['status']) for p in paired)/len(paired) if paired else None,
        rows=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['no-index', 'semantic'], required=True)
    parser.add_argument('--db', help='Fresh scratch index directory (semantic only)')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    benchmark = load_benchmark()
    if args.mode == 'semantic':
        if not args.db or Path(args.db).exists():
            parser.error('--db must be a new directory, to avoid modifying user indexes')
        from app.verified_rag import ingest_verified, retrieve_verified
        started = time.perf_counter()
        ingest_verified(args.db)
        setup_ms = (time.perf_counter()-started)*1000
        def search(q, k):
            hits = retrieve_verified(q, args.db, limit=k)
            return dict(status='retrieved' if hits else 'insufficient_evidence', citations=hits)
    else:
        setup_ms = None
        # Real missing-index path, independent of any ambient DB configuration.
        from app.evidence_tools import search_evidence
        os.environ.pop('PHARMA_VERIFIED_DB', None)
        def search(q, k):
            return search_evidence(q, k)
    report = evaluate(benchmark['cases'], search)
    try:
        commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = 'unknown'
    packages = {}
    for name in ('chromadb','sentence-transformers','torch'):
        try: packages[name] = version(name)
        except PackageNotFoundError: packages[name] = None
    report.update(schema_version=1, mode=args.mode, benchmark_version=benchmark['version'],
        benchmark_sha256=digest(BENCHMARK), corpus_collection=collection_name(load_corpus()),
        model=MODEL, model_revision=MODEL_REVISION, max_distance=.35, setup_ms=setup_ms, commit=commit,
        python=platform.python_version(), packages=packages,
        limitations='Development snapshot, author-labelled, no synthesis or clinical correctness scoring. Latency excludes ingestion; first query may be cold. No-index is an infrastructure diagnostic, not retrieval quality.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps(report['metrics'], indent=2))
    # Fail closed for semantic infrastructure failures; poor quality remains visible, not hidden.
    if args.mode == 'semantic' and report['metrics']['operational_rate'] != 1:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
