"""Build a portable static demo from the hash-validated public snapshot."""
import json
import pathlib
import shutil
import sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from app.verified_rag import load_corpus
from app.evaluation import load_benchmark


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    for name in ('index.html','app.js','style.css'):
        shutil.copyfile(ROOT/'frontend'/name, output/name)
    report_path=ROOT/'frontend/evaluation-report.json'
    report=json.loads(report_path.read_text()) if report_path.exists() else None
    sources=load_corpus()
    for d in sources:
        lines=(ROOT/'documents/verified'/d['file']).read_text().strip().splitlines()
        d['display']={'en':lines[0], 'ja':lines[1]}
    data=dict(sources=sources, benchmark=load_benchmark(), report=report)
    (output/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (output/'.nojekyll').touch()

if __name__=='__main__':
    build(pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'dist')
