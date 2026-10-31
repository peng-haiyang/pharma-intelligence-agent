'use strict';
const $=s=>document.querySelector(s);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
let data;
let service=null, currentRun=null;
const localBackend=location.pathname.startsWith('/demo/');
const stages=[
 ['Original','Preserved Japan market prototype','The original hosted Japan outlook remains separate and untouched. Its editable source was not recovered.'],
 ['Stage 1','API foundation','Health checks, bounded question input, and an explicit no-evidence response.'],
 ['Stage 2 → 2C','Verified retrieval','Semantic retrieval over three attributed bilingual public summaries, with source URLs and content digests. Legacy unverified retrieval remains isolated.'],
 ['Stage 3A','Read-only evidence tools','MCP search and document lookup expose validated corpus material to clients.'],
 ['Stage 3B','Bounded orchestration','A deterministic search-and-hydrate workflow with tool budgets, timeouts, and traces. No autonomous planner or answer synthesis.'],
 ['Stage 4A','Evaluation + visible workbench','A bilingual development benchmark; retrieval, citation, abstention and latency reports; source browser and case inspector. The first evaluation milestone.'],
 ['Stage 4B','Live question desk and evidence activity','Ask your own English or Japanese question on the hosted demo. A bounded lexical retriever searches the approved snapshot and streams scope, search and source-integrity events. Separate from the Python semantic engine.'],
 ['Next / proposed','Independent review and broader evidence','Review benchmark labels with bilingual domain experts, add approved sources and held-out cases, calibrate retrieval thresholds, then assess whether grounded synthesis is ready. No release promise or completion claim.']
];
function sources(){
 $('#sources').replaceChildren(...data.sources.map(d=>{
  const n=el('article',undefined,'card');n.append(el('div',d.publisher,'publisher'),el('h3',d.title));
  n.append(el('p',d.display[$('#language').value]));
  const a=el('a','Publisher source ↗');a.href=d.url;a.target='_blank';a.rel='noopener noreferrer';n.append(a,el('small',`Reviewed ${d.verified} · ${d.section}`),el('p',`SHA-256 ${d.sha256}`,'hash'));return n;
 }));
 const questions=data.benchmark.cases.filter(c=>c.language===$('#language').value);
 $('#question').replaceChildren(...questions.map(c=>{const o=el('option',c.question);o.value=c.id;return o;}));reference();
}
function reference(){const c=data.benchmark.cases.find(c=>c.id===$('#question').value);$('#reference').textContent='Selected example: '+c.question+' — '+(c.expected_abstain?'Gold label: abstain. '+c.rationale:'Gold reference (authored benchmark label, not a model response): '+c.reference);$('#question-text').value=c.question;}
function cases(){const kind=$('#case-filter').value;$('#cases').replaceChildren(...data.benchmark.cases.filter(c=>kind==='all'||(kind==='abstain'?c.expected_abstain:!c.expected_abstain)).map(c=>{const row=el('tr');const observed=data.report?.rows.find(r=>r.id===c.id);row.append(el('td',c.id),el('td',c.question),el('td',c.expected_abstain?'Abstain / evidence insufficient':c.expected_ids.join(', ')),el('td',observed?.status??'Not run'));return row;}));}
function evaluation(){const r=data.report;$('#report-label').textContent=r?`Stored Python semantic report (not the hosted lexical engine): ${r.mode}. ${r.mode==='semantic'?'Real semantic retrieval; no LLM or mock outputs.':'Missing-index diagnostic. No model retrieval was run; these are not quality results.'}`:'No evaluation report supplied. Run the evaluator to populate this panel.';if(!r)return;
 const m=r.metrics;const number=v=>v==null?'N/A':`${Math.round(v*100)}%`;
 for(const [label,value] of [['Recall @ 3',number(m.recall_at_k)],['MRR @ 3',m.mrr_at_k?.toFixed(3)??'N/A'],['Citation provenance',number(m.citation_provenance_precision)],['Citation relevance',number(m.citation_relevance_precision)],['Correct abstention',number(m.abstention_accuracy)],['Operational availability',number(m.operational_rate)]]){const n=el('article',undefined,'card');n.append(el('div',label,'publisher'),el('div',value,'metric'));$('#metrics').append(n);}
 $('#report-meta').textContent=`p50 ${m.latency_p50_ms} ms · p95 ${m.latency_p95_ms} ms · ${r.model} · distance ≤ ${r.max_distance} · commit ${r.commit.slice(0,12)}. Stored measurements, not live timings. Ingestion/model setup excluded; first query may be cold.`;
}
async function init(){try{const response=await fetch('data.json');if(!response.ok)throw Error('Snapshot could not be loaded');data=await response.json();sources();evaluation();cases();
 for(const [stage,title,description] of stages){const n=el('article',undefined,'stage'),body=el('div');body.append(el('h3',title),el('p',description));n.append(el('strong',stage),body);$('#timeline').append(n);}
 document.querySelectorAll('nav button').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('nav button').forEach(x=>{x.setAttribute('aria-pressed',String(x===b));$('#'+x.dataset.view).hidden=x!==b;});}));
 $('#language').addEventListener('change',sources);$('#question').addEventListener('change',reference);$('#case-filter').addEventListener('change',cases);
 await configureService();
 $('#question-form').addEventListener('submit',runQuestion);
 $('#cancel').addEventListener('click',()=>currentRun?.abort());
 }catch(e){$('#error').hidden=false;$('#error').textContent=e.message;}}
async function configureService(){
 try{const response=await fetch('/api/demo/config');if(response.ok){const config=await response.json();if(config.engine==='snapshot-bm25-v1'&&config.stream)service=config;}}catch{}
 if(service){$('#mode').textContent='Live hosted retrieval · approved dated snapshot';$('#api-note').textContent='Hosted bilingual lexical search (snapshot-bm25-v1). Real source checks stream below. No live publisher fetch, semantic model, or generated answer. Questions are not stored by this app.';$('#run').textContent='Ask & inspect evidence';$('#run').disabled=false;}
 else if(localBackend){$('#mode').textContent='Local Python semantic retrieval · dated snapshot';$('#api-note').textContent='This local backend uses the Python semantic index. It returns the final response only; hosted streaming activity is not available here.';$('#run').textContent='Ask local semantic retriever';$('#run').disabled=false;}
 else{$('#mode').textContent='Offline public snapshot';$('#api-note').textContent='Static preview only. Open the hosted development Site to ask questions with live activity.';$('#run').textContent='No live retrieval service';}
}
function activity(event){const n=el('li');n.dataset.status=event.status;n.append(el('strong',`${event.step} · ${event.status}`),el('span',event.detail),el('small',`${event.elapsed_ms} ms`));$('#activity').append(n);}
function renderResult(result){
 const target=$('#answer');target.replaceChildren();
 target.append(el('strong',result.status==='retrieved'?'Relevant snapshot evidence':result.status==='unavailable'?'Evidence service unavailable':'Insufficient evidence'));
 target.append(el('p',`Reason: ${result.reason??'unspecified'}. Engine: ${result.engine??'Python semantic retrieval'}.`));
 for(const hit of result.citations??[]){const card=el('article',undefined,'card');card.append(el('h3',hit.title??hit.id),el('p',hit.passage));
  // Treat every response field as text; link only to approved HTTPS publisher origins.
  try{const url=new URL(hit.url);if(url.protocol==='https:'&&['www.pmda.go.jp','www.mhlw.go.jp','www.jrs.or.jp'].includes(url.host)){const a=el('a','Publisher source ↗');a.href=url.href;a.target='_blank';a.rel='noopener noreferrer';card.append(a);}}catch{}
  card.append(el('small',`Snapshot verified ${hit.verified??'unknown'} · ${hit.section??''}`));target.append(card);
 }
 target.append(el('p','Evidence passages only. The system does not generate a clinical or commercial recommendation.'));
 $('#raw').hidden=false;$('#result').textContent=JSON.stringify(result,null,2);
}
async function runQuestion(event){
 event.preventDefault();if(currentRun||(!service&&!localBackend))return;
 const controller=new AbortController();currentRun=controller;for(const selector of ['#question-text','#question','#language'])$(selector).disabled=true;$('#run').disabled=true;$('#cancel').disabled=false;$('#activity').replaceChildren();$('#answer').textContent='Request in progress…';$('#raw').hidden=true;
 let receivedResult=false;
 try{
  const question=$('#question-text').value.trim();
  const response=await fetch(service?'/api/demo/investigate':'/api/v2/questions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question}),signal:controller.signal});
  if(!response.ok){let message=`HTTP ${response.status}`;try{message+=(": "+(await response.json()).error);}catch{}throw Error(message);}
  if(!service){renderResult(await response.json());receivedResult=true;return;}
  if(!response.headers.get('Content-Type')?.includes('text/event-stream')||!response.body)throw Error('Expected a streamed activity response');
  const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='';
  try{for(;;){const {done,value}=await reader.read();if(done)break;buffer+=decoder.decode(value,{stream:true});
   let boundary;while((boundary=buffer.indexOf('\n\n'))>=0){const frame=buffer.slice(0,boundary);buffer=buffer.slice(boundary+2);const type=frame.match(/^event: (.+)$/m)?.[1];const payload=frame.match(/^data: (.+)$/m)?.[1];if(!payload)continue;const parsed=JSON.parse(payload);
    if(type==='activity')activity(parsed);else if(type==='result'){renderResult(parsed);receivedResult=true;}else if(type==='error')throw Error(parsed.error);
   }
  }}finally{reader.releaseLock();}
  if(!receivedResult)throw Error('Stream ended before a final result arrived');
 }catch(e){$('#answer').textContent=controller.signal.aborted?'Request cancelled. No final result is claimed.':`Request failed: ${e.message}`;activity({step:'request',status:controller.signal.aborted?'cancelled':'failed',detail:controller.signal.aborted?'You cancelled this request.':'The request did not complete successfully.',elapsed_ms:0});}
 finally{currentRun=null;for(const selector of ['#question-text','#question','#language'])$(selector).disabled=false;$('#run').disabled=false;$('#cancel').disabled=true;}
}
init();
