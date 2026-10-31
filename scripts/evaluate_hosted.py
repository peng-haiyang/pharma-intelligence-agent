"""Evaluate the hosted engine with the Stage 4A metric implementation."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from build_demo import ROOT
sys.path.insert(0,str(ROOT/'backend'))
from app.evaluation import evaluate, load_benchmark, digest, BENCHMARK
from app.verified_rag import load_corpus,collection_name
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--node',default='node')
p.add_argument('--output',type=Path,default=ROOT/'benchmarks/hosted-lexical-report.json')
args=p.parse_args()
measured=json.loads(subprocess.check_output([args.node,str(ROOT/'hosted/evaluate.mjs')],cwd=ROOT,text=True))
cases=load_benchmark()['cases']
results={r['id']:r for r in measured}
question_to_case={c['question']:c['id'] for c in cases}
times=[]
for c in cases:
    times.extend([0,results[c['id']]['elapsed_ms']/1000])
clock=iter(times)
report=evaluate(cases,lambda q,k:results[question_to_case[q]]['result'],clock=lambda:next(clock))
report.update(mode='hosted-lexical',engine='snapshot-bm25-v1',benchmark_sha256=digest(BENCHMARK),corpus_collection=collection_name(load_corpus()),limitations='Author-labelled development set; exclusion rules and overlap thresholds are not clinically validated. In-process engine timings exclude HTTP transport and hosting cold start. Separate engine from the Python semantic benchmark.')
args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report['metrics'],indent=2))
