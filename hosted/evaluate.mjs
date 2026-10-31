// Benchmark labels are used only by evaluation, never imported into the live engine.
import {readFile} from 'node:fs/promises';
import {investigate} from './engine.mjs';
const root=new URL('../',import.meta.url);
const snapshot=JSON.parse(await readFile(new URL('dist/data.json',root),'utf8'));
const docs=await Promise.all(snapshot.sources.map(async d=>({...d,source_text:await readFile(new URL('documents/verified/'+d.file,root),'utf8')})));
const rows=[];
for(const c of snapshot.benchmark.cases){const start=performance.now();const result=await investigate(c.question,docs);rows.push({id:c.id,result,elapsed_ms:performance.now()-start});}
process.stdout.write(JSON.stringify(rows));
