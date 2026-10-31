import copy
import pytest
from app.evaluation import evaluate, load_benchmark, percentile
from app.verified_rag import load_corpus


def cases():
    return load_benchmark()['cases']


def test_bilingual_snapshot_and_gold_are_pinned():
    data = load_benchmark()
    assert len(data['cases']) == 22
    assert sum(c['expected_abstain'] for c in data['cases']) == 12


def test_hand_computed_metrics_with_irrelevant_and_forged_citations():
    positive, negative = cases()[0], cases()[-1]
    docs = {d['id']:d for d in load_corpus()}
    good = docs[positive['expected_ids'][0]]
    other = docs['jrs-copd']
    forged = {**good, 'url':'https://example.com/fake'}
    times=iter([0, .01, 1, 1.03])
    report=evaluate([positive,negative], lambda q,k:dict(status='retrieved',citations=[other,forged,good]),clock=lambda:next(times))
    m=report['metrics']
    assert m['recall_at_k']==1 and m['mrr_at_k']==pytest.approx(1/3)
    assert m['citation_provenance_precision']==pytest.approx(2/3)
    assert m['citation_relevance_precision']==pytest.approx(1/6)
    assert m['abstention_accuracy']==0
    assert m['latency_p50_ms']==10 and m['latency_p95_ms']==30


def test_unavailability_and_exceptions_do_not_receive_abstention_credit():
    for search in (lambda q,k:dict(status='unavailable',citations=[]),lambda q,k:1/0):
        m=evaluate(cases(),search)['metrics']
        assert m['operational_rate']==0 and m['abstention_accuracy']==0
        assert m['recall_at_k']==0 and m['citation_provenance_precision'] is None


def test_empty_evidence_abstention_and_bilingual_breakdown():
    r=evaluate(cases(),lambda q,k:dict(status='insufficient_evidence',citations=[]))
    assert r['metrics']['abstention_accuracy']==1
    assert r['metrics']['answerable_coverage']==0
    assert r['by_language']['ja']['cases']==11
    assert r['pair_outcome_agreement']==1


def test_tampered_gold_rejected(tmp_path):
    import json
    d=copy.deepcopy(load_benchmark())
    d['cases'][0]['source_sha256']='0'*64
    path=tmp_path/'cases.json'
    path.write_text(json.dumps(d))
    with pytest.raises(ValueError,match='Stale gold'): load_benchmark(path)


@pytest.mark.parametrize('result',[{}, {'status':'retrieved','citations':[]}, {'status':'insufficient_evidence','citations':[{}]}, {'status':'retrieved','citations':['bad']}])
def test_malformed_results_fail_closed(result):
    assert evaluate(cases()[:1],lambda q,k:result)['rows'][0]['status']=='error'


def test_nearest_rank_and_k_bounds():
    assert percentile([], .95) is None
    assert percentile([9,1,2],.5)==2
    with pytest.raises(ValueError): evaluate([],lambda q,k:None,k=0)


def test_malformed_citation_keys_are_invalid_not_a_crash():
    r=evaluate(cases()[:1],lambda q,k:dict(status='retrieved',citations=[{'id':[], 'chunk':{}}]))
    assert r['metrics']['citation_provenance_precision']==0


@pytest.mark.parametrize('field,value', [
    ('url', 'https://example.com/fake'), ('sha256', '0'*64),
    ('passage', 'Invented evidence'), ('publisher', 'Forged'),
    ('section', 'Invented section'), ('chunk', 999),
])
def test_forged_gold_id_never_receives_retrieval_credit(field, value):
    positive = cases()[0]
    good = next(d for d in load_corpus() if d['id'] == positive['expected_ids'][0])
    forged = {**good, field: value}
    report = evaluate([positive], lambda q,k: dict(status='retrieved', citations=[forged]))
    assert report['metrics']['recall_at_k'] == 0
    assert report['metrics']['mrr_at_k'] == 0
    assert report['metrics']['citation_provenance_precision'] == 0
    # Coverage describes whether anything was returned, not trustworthy relevance.
    assert report['metrics']['answerable_coverage'] == 1
    assert report['rows'][0]['retrieved_ids'] == [good['id']]
    assert report['rows'][0]['trusted_retrieved_ids'] == []


def test_forged_duplicate_does_not_promote_valid_citation_rank():
    positive = cases()[0]
    good = next(d for d in load_corpus() if d['id'] == positive['expected_ids'][0])
    forged = {**good, 'passage': 'fabricated'}
    result = dict(status='retrieved', citations=[forged, good, good])
    report = evaluate([positive], lambda q,k: result)
    assert report['metrics']['recall_at_k'] == 1
    assert report['metrics']['mrr_at_k'] == .5
    assert report['rows'][0]['trusted_retrieved_ids'] == [good['id']]
    # A valid citation outside the requested k earns no recall/rank credit.
    top_one = evaluate([positive], lambda q,k: result, k=1)
    assert top_one['metrics']['recall_at_k'] == 0
    assert top_one['metrics']['mrr_at_k'] == 0


def test_valid_duplicates_preserve_original_slots_and_single_recall():
    positive = cases()[0]
    docs = {d['id']: d for d in load_corpus()}
    good = docs[positive['expected_ids'][0]]
    unrelated = docs['jrs-copd']
    report = evaluate([positive], lambda q,k: dict(status='retrieved', citations=[unrelated, unrelated, good]))
    assert report['metrics']['recall_at_k'] == 1
    assert report['metrics']['mrr_at_k'] == pytest.approx(1/3)
