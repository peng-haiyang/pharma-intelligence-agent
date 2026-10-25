import multiprocessing as mp
import time
import pytest
from app.agent_harness import Limits, Run, Tool, ToolRegistry, evidence_registry, investigate


def echo(**kwargs):
    return {'status': 'found', 'value': kwargs}


def broken(**kwargs):
    raise RuntimeError('private secret path')


def slow(**kwargs):
    time.sleep(10)
    return {}


def huge(**kwargs):
    return {'value': 'x' * 1000}


def non_json(**kwargs):
    return {'value': object()}


def search(**kwargs):
    return {'status': 'retrieved', 'citations': [{'id': 'jrs-copd'}, {'id': 'jrs-copd'}]}


def missing(**kwargs):
    return {'status': 'not_found'}


def malformed(**kwargs):
    return {'status': 'retrieved', 'citations': [{'unexpected': 'shape'}]}


def registry(handler=echo):
    return ToolRegistry([Tool('echo', handler, frozenset({'value'}), frozenset({'value'}))])


def workflow(search_handler=search, document_handler=echo):
    return ToolRegistry([
        Tool('search_verified_evidence', search_handler, frozenset({'question', 'limit'}), frozenset({'question'})),
        Tool('get_verified_document', document_handler, frozenset({'document_id'}), frozenset({'document_id'}))])


def test_registry_and_limits():
    assert len(evidence_registry().names()) == 2
    tool = Tool('echo', echo, frozenset(), frozenset())
    with pytest.raises(ValueError):
        ToolRegistry([tool, tool])
    for options in ({'max_calls': True}, {'max_calls': 0}, {'timeout_seconds': float('nan')},
                    {'tool_timeout_seconds': float('inf')}, {'max_result_bytes': 0}):
        with pytest.raises(ValueError):
            Limits(**options)


def test_success_and_trace_privacy():
    run = Run(registry())
    result = run.call('echo', {'value': 'private question'})
    assert result['ok'] and result['result']['value']['value'] == 'private question'
    assert run.trace[0]['outcome'] == 'ok'
    assert 'private question' not in str(run.trace)
    assert run.report('complete')['run_id']


def test_validation_and_call_budget():
    run = Run(registry(), Limits(max_calls=3))
    assert run.call('unknown', {})['error']['code'] == 'unknown_tool'
    assert run.call('echo', {})['error']['code'] == 'invalid_arguments'
    assert run.call('echo', {'value': 1, 'extra': 2})['error']['code'] == 'invalid_arguments'
    assert run.call('echo', {'value': 1})['error']['code'] == 'call_limit'
    assert len(run.trace) == 3


@pytest.mark.parametrize('handler,code', [(broken, 'tool_exception'), (huge, 'result_too_large'),
                                         (non_json, 'tool_exception')])
def test_structured_failure(handler, code):
    result = Run(registry(handler), Limits(max_result_bytes=128)).call('echo', {'value': 1})
    assert result == {'ok': False, 'error': {'code': code}}
    assert 'secret' not in str(result)


def test_timeout_terminates_worker():
    before = {p.pid for p in mp.active_children()}
    start = time.monotonic()
    result = Run(registry(slow), Limits(tool_timeout_seconds=0.3)).call('echo', {'value': 1})
    assert result['error']['code'] == 'tool_timeout'
    assert time.monotonic() - start < 4
    assert {p.pid for p in mp.active_children()} == before


def test_run_deadline():
    run = Run(registry(), Limits(timeout_seconds=0.01))
    time.sleep(0.02)
    assert run.call('echo', {'value': 1})['error']['code'] == 'run_timeout'


def test_deadline_during_tool():
    result = Run(registry(slow), Limits(timeout_seconds=0.3, tool_timeout_seconds=2)).call('echo', {'value': 1})
    assert result['error']['code'] == 'run_timeout'


def test_argument_size_and_non_json():
    for value in ('x' * 9000, object(), float('nan')):
        assert Run(registry()).call('echo', {'value': value})['error']['code'] == 'invalid_arguments'


def test_orchestration_deduplicates():
    result = investigate('COPD treatment', registry=workflow())
    assert result['status'] == 'complete'
    assert len(result['documents']) == 1
    assert len(result['trace']) == 2


def test_partial_and_malformed():
    result = investigate('COPD treatment', registry=workflow(), limits=Limits(max_calls=1))
    assert result['status'] == 'partial' and result['error']['code'] == 'call_limit'
    assert investigate('COPD treatment', registry=workflow(document_handler=missing))['status'] == 'partial'
    assert investigate('COPD treatment', registry=workflow(search_handler=malformed))['error']['code'] == 'invalid_tool_result'
    assert investigate('COPD treatment', registry=workflow(search_handler=broken))['status'] == 'failed'


def test_actual_tools_abstain_and_read_document(monkeypatch):
    monkeypatch.delenv('PHARMA_VERIFIED_DB', raising=False)
    result = investigate('What does PMDA publish?')
    assert result['status'] == 'abstained'
    assert result['evidence']['reason'] == 'semantic_index_not_configured'
    document = Run(evidence_registry()).call('get_verified_document', {'document_id': 'jrs-copd'})
    assert document['result']['status'] == 'found'
