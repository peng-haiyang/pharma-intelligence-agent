"""Deterministic evidence orchestration with a trusted registry and process budgets."""
from dataclasses import asdict, dataclass
import json
import multiprocessing as mp
import time
from uuid import uuid4
from app.evidence_tools import get_evidence_document, search_evidence


@dataclass(frozen=True)
class Tool:
    name: str
    handler: object
    parameters: frozenset[str]
    required: frozenset[str]


class ToolRegistry:
    def __init__(self, tools):
        self._tools = {}
        for tool in tools:
            if tool.name in self._tools or not callable(tool.handler):
                raise ValueError('Duplicate name or invalid handler')
            if not tool.required <= tool.parameters:
                raise ValueError('Invalid schema')
            self._tools[tool.name] = tool

    def get(self, name):
        return self._tools.get(name)

    def names(self):
        return sorted(self._tools)


def evidence_registry():
    return ToolRegistry([
        Tool('search_verified_evidence', search_evidence,
             frozenset({'question', 'limit'}), frozenset({'question'})),
        Tool('get_verified_document', get_evidence_document,
             frozenset({'document_id'}), frozenset({'document_id'})),
    ])


@dataclass(frozen=True)
class Limits:
    max_calls: int = 4
    timeout_seconds: float = 30
    tool_timeout_seconds: float = 15
    max_result_bytes: int = 256_000

    def __post_init__(self):
        for value, low, high in ((self.max_calls, 1, 20), (self.max_result_bytes, 128, 1_000_000)):
            if type(value) is not int or not low <= value <= high:
                raise ValueError('Invalid integer limit')
        for value in (self.timeout_seconds, self.tool_timeout_seconds):
            if type(value) not in (int, float) or not 0 < value <= 300:
                raise ValueError('Invalid time limit')


def _worker(connection, handler, arguments, max_bytes):
    try:
        result = handler(**arguments)
        if not isinstance(result, dict):
            raise ValueError('Tool results must be objects')
        payload = json.dumps(result, allow_nan=False).encode()
        connection.send(('ok', payload) if len(payload) <= max_bytes else ('result_too_large', None))
    except Exception:
        connection.send(('tool_exception', None))
    finally:
        connection.close()


class Run:
    """Single-use run budget. Spawn workers require module-level handlers.

    Workers are terminated on timeout. This is not an OS security sandbox:
    handlers are trusted code and must not spawn descendants.
    """
    def __init__(self, registry, limits=None):
        self.registry = registry
        self.limits = limits or Limits()
        self.run_id = str(uuid4())
        self.started = time.monotonic()
        self.trace = []

    def call(self, name, arguments):
        start = time.monotonic()
        error, result = None, None
        remaining = self.limits.timeout_seconds - (start - self.started)
        if len(self.trace) >= self.limits.max_calls:
            return {'ok': False, 'error': {'code': 'call_limit'}}
        tool = self.registry.get(name) if isinstance(name, str) else None
        if remaining <= 0:
            error = 'run_timeout'
        elif tool is None:
            error = 'unknown_tool'
        elif not isinstance(arguments, dict) or not tool.required <= arguments.keys() <= tool.parameters:
            error = 'invalid_arguments'
        else:
            try:
                if len(json.dumps(arguments, allow_nan=False).encode()) > 8192:
                    error = 'invalid_arguments'
            except (TypeError, ValueError):
                error = 'invalid_arguments'
            if error is None:
                context = mp.get_context('spawn')
                receiver, sender = context.Pipe(duplex=False)
                process = context.Process(target=_worker,
                    args=(sender, tool.handler, arguments, self.limits.max_result_bytes))
                try:
                    process.start()
                    sender.close()
                    if receiver.poll(min(remaining, self.limits.tool_timeout_seconds)):
                        code, payload = receiver.recv()
                        if code == 'ok':
                            result = json.loads(payload)
                        else:
                            error = code
                    else:
                        error = 'tool_timeout' if remaining >= self.limits.tool_timeout_seconds else 'run_timeout'
                except Exception:
                    error = 'tool_exception'
                finally:
                    if process.pid is not None:
                        if process.is_alive():
                            process.terminate()
                        process.join(timeout=1)
                        if process.is_alive():
                            process.kill()
                            process.join(timeout=1)
                        process.close()
                    receiver.close()
                    sender.close()
        response = {'ok': False, 'error': {'code': error}} if error else {'ok': True, 'result': result}
        self.trace.append({'step': len(self.trace) + 1, 'tool': name if tool else 'unregistered',
                           'elapsed_ms': round((time.monotonic() - start) * 1000),
                           'outcome': error or 'ok',
                           'tool_status': result.get('status') if result else None})
        return response

    def report(self, status, **fields):
        return {'run_id': self.run_id, 'status': status, **fields,
                'trace': list(self.trace), 'limits': asdict(self.limits)}


def investigate(question, *, registry=None, limits=None):
    """Search once and hydrate distinct cited documents; no synthesis or retries."""
    run = Run(registry or evidence_registry(), limits)
    search = run.call('search_verified_evidence', {'question': question, 'limit': 3})
    if not search['ok']:
        return run.report('failed', error=search['error'])
    evidence = search['result']
    if evidence.get('status') != 'retrieved':
        return run.report('abstained', evidence=evidence, documents=[])
    citations = evidence.get('citations')
    if not isinstance(citations, list) or not citations:
        return run.report('failed', error={'code': 'invalid_tool_result'})
    documents, seen = [], set()
    for citation in citations:
        if not isinstance(citation, dict) or not isinstance(citation.get('id'), str):
            return run.report('failed', error={'code': 'invalid_tool_result'})
        doc_id = citation['id']
        if doc_id in seen:
            continue
        seen.add(doc_id)
        document = run.call('get_verified_document', {'document_id': doc_id})
        if not document['ok'] or document['result'].get('status') != 'found':
            return run.report('partial', evidence=evidence, documents=documents,
                              error=document.get('error', {'code': 'document_unavailable'}))
        documents.append(document['result'])
    return run.report('complete', evidence=evidence, documents=documents)
