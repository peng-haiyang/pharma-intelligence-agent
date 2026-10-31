// Bundled into a single self-contained ESM Worker by scripts/build_hosted.py.
import {investigate,ENGINE} from './engine.mjs';
const HEADERS={'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Cache-Control':'no-store','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; frame-ancestors 'self'; form-action 'self'"};
function json(value,status=200){return new Response(JSON.stringify(value),{status,headers:{...HEADERS,'Content-Type':'application/json; charset=utf-8'}});}
async function boundedBody(request){
  const reader=request.body?.getReader();if(!reader)throw Error('empty_body');let size=0;const chunks=[];
  try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>8192){await reader.cancel();throw Error('body_too_large');}chunks.push(value);}}finally{reader.releaseLock();}
  const all=new Uint8Array(size);let offset=0;for(const c of chunks){all.set(c,offset);offset+=c.byteLength;}return JSON.parse(new TextDecoder().decode(all));
}
export function createWorker(assets,docs){return {async fetch(request){
  const url=new URL(request.url);
  if(url.pathname==='/api/demo/config'){
    if(request.method!=='GET')return json({error:'method_not_allowed'},405);
    return json({engine:ENGINE,stream:true,corpus_size:docs.length,source_freshness:'snapshot',synthesis:'disabled',question_storage:'none'});
  }
  if(url.pathname==='/api/demo/investigate'){
    if(request.method!=='POST')return json({error:'method_not_allowed'},405);
    if((request.headers.get('Origin')&&request.headers.get('Origin')!==url.origin)||request.headers.get('Sec-Fetch-Site')==='cross-site')return json({error:'cross_origin_not_allowed'},403);
    if(!(request.headers.get('Content-Type')||'').toLowerCase().startsWith('application/json'))return json({error:'json_required'},415);
    let payload;try{payload=await boundedBody(request);}catch(e){return json({error:e.message==='body_too_large'?'body_too_large':'invalid_json'},e.message==='body_too_large'?413:400);}
    if(!payload||Object.keys(payload).length!==1||typeof payload.question!=='string'||payload.question.trim().length<5||payload.question.length>2000)return json({error:'question_must_be_5_to_2000_characters'},422);
    const enc=new TextEncoder();let cancelled=false;
    const stream=new ReadableStream({
      async start(controller){
        const send=(event,data)=>{if(!cancelled)controller.enqueue(enc.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`));};
        try{const result=await investigate(payload.question.trim(),docs,event=>send('activity',event));send('result',result);}
        catch{send('error',{error:'investigation_failed'});}
        finally{if(!cancelled)controller.close();}
      },cancel(){cancelled=true;}
    });
    return new Response(stream,{headers:{...HEADERS,'Content-Type':'text/event-stream; charset=utf-8','X-Accel-Buffering':'no'}});
  }
  if(request.method!=='GET'&&request.method!=='HEAD')return json({error:'method_not_allowed'},405);
  const path=url.pathname==='/'?'/index.html':url.pathname;
  const asset=assets[path];if(!asset)return json({error:'not_found'},404);
  return new Response(request.method==='HEAD'?null:asset.body,{headers:{...HEADERS,'Content-Type':asset.type}});
}};}
