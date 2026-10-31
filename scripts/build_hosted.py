"""Bundle the hosted live demo, including only hash-validated public summaries."""
import argparse
import json
from pathlib import Path
from build_demo import build, ROOT


def bundle(output):
    # Build a separate static preview so local backend behavior stays available.
    static=ROOT/'dist'
    build(static)
    snapshot=json.loads((static/'data.json').read_text())
    assets={}
    types={'index.html':'text/html; charset=utf-8','app.js':'text/javascript; charset=utf-8','style.css':'text/css; charset=utf-8','data.json':'application/json; charset=utf-8'}
    for name,kind in types.items():
        assets['/'+name]={'type':kind,'body':(static/name).read_text()}
    docs=[]
    for source in snapshot['sources']:
        docs.append({**source,'source_text':(ROOT/'documents/verified'/source['file']).read_text()})
    engine=(ROOT/'hosted/engine.mjs').read_text()
    worker=(ROOT/'hosted/worker.mjs').read_text().replace("import {investigate,ENGINE} from './engine.mjs';",'')
    code=engine+'\n'+worker+'\nconst ASSETS='+json.dumps(assets,ensure_ascii=False)+';\nconst DOCS='+json.dumps(docs,ensure_ascii=False)+';\nexport default createWorker(ASSETS,DOCS);\n'
    (output/'server').mkdir(parents=True,exist_ok=True)
    (output/'server/index.js').write_text(code)
    print(f'Built live Worker: {output}/server/index.js')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'dist-hosted')
    bundle(p.parse_args().output)
