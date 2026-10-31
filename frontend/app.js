'use strict';
const $=s=>document.querySelector(s);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
let data;
const live=location.pathname.startsWith('/demo/');
const stages=[
 ['Original','Preserved Japan market prototype','The original hosted Japan outlook remains separate and untouched. Its editable source was not recovered.'],
 ['Stage 1','API foundation','Health checks, bounded question input, and an explicit no-evidence response.'],
 ['Stage 2 → 2C','Verified retrieval','Semantic retrieval over three attributed bilingual public summaries, with source URLs and content digests. Legacy unverified retrieval remains isolated.'],
 ['Stage 3A','Read-only evidence tools','MCP search and document lookup expose validated corpus material to clients.'],
 ['Stage 3B','Bounded orchestration','A deterministic search-and-hydrate workflow with tool budgets, timeouts, and traces. No autonomous planner or answer synthesis.'],
 ['Stage 4A','Evaluation + visible workbench','A bilingual development benchmark; retrieval, citation, abstention and latency reports; source browser and case inspector. This is the current development preview.'],
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
function reference(){const c=data.benchmark.cases.find(c=>c.id===$('#question').value);$('#reference').textContent=c.expected_abstain?'Gold label: abstain. '+c.rationale:'Gold reference (authored benchmark label, not a model response): '+c.reference;$('#result').hidden=true;}
function cases(){const kind=$('#case-filter').value;$('#cases').replaceChildren(...data.benchmark.cases.filter(c=>kind==='all'||(kind==='abstain'?c.expected_abstain:!c.expected_abstain)).map(c=>{const row=el('tr');const observed=data.report?.rows.find(r=>r.id===c.id);row.append(el('td',c.id),el('td',c.question),el('td',c.expected_abstain?'Abstain / evidence insufficient':c.expected_ids.join(', ')),el('td',observed?.status??'Not run'));return row;}));}
function evaluation(){const r=data.report;$('#report-label').textContent=r?`Stored report: ${r.mode}. ${r.mode==='semantic'?'Real semantic retrieval; no LLM or mock outputs.':'Missing-index diagnostic. No model retrieval was run; these are not quality results.'}`:'No evaluation report supplied. Run the evaluator to populate this panel.';if(!r)return;
 const m=r.metrics;const number=v=>v==null?'N/A':`${Math.round(v*100)}%`;
 for(const [label,value] of [['Recall @ 3',number(m.recall_at_k)],['MRR @ 3',m.mrr_at_k?.toFixed(3)??'N/A'],['Citation provenance',number(m.citation_provenance_precision)],['Citation relevance',number(m.citation_relevance_precision)],['Correct abstention',number(m.abstention_accuracy)],['Operational availability',number(m.operational_rate)]]){const n=el('article',undefined,'card');n.append(el('div',label,'publisher'),el('div',value,'metric'));$('#metrics').append(n);}
 $('#report-meta').textContent=`p50 ${m.latency_p50_ms} ms · p95 ${m.latency_p95_ms} ms · ${r.model} · distance ≤ ${r.max_distance} · commit ${r.commit.slice(0,12)}. Stored measurements, not live timings. Ingestion/model setup excluded; first query may be cold.`;
}
async function init(){try{const response=await fetch('data.json');if(!response.ok)throw Error('Snapshot could not be loaded');data=await response.json();sources();evaluation();cases();
 for(const [stage,title,description] of stages){const n=el('article',undefined,'stage'),body=el('div');body.append(el('h3',title),el('p',description));n.append(el('strong',stage),body);$('#timeline').append(n);}
 document.querySelectorAll('nav button').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('nav button').forEach(x=>{x.setAttribute('aria-pressed',String(x===b));$('#'+x.dataset.view).hidden=x!==b;});}));
 $('#language').addEventListener('change',sources);$('#question').addEventListener('change',reference);$('#case-filter').addEventListener('change',cases);
 if(live){$('#mode').textContent='Backend connected mode · dated public corpus';$('#run').disabled=false;$('#run').textContent='Run real verified retrieval';$('#api-note').textContent='Calls this backend’s /api/v2/questions. No synthesis. A missing or failed index is reported explicitly.';}
 $('#run').addEventListener('click',async()=>{const button=$('#run');button.disabled=true;$('#result').hidden=false;$('#result').textContent='Retrieving…';try{const c=data.benchmark.cases.find(c=>c.id===$('#question').value);const response=await fetch('/api/v2/questions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:c.question})});if(!response.ok)throw Error(`API returned ${response.status}`);$('#result').textContent=JSON.stringify(await response.json(),null,2);}catch(e){$('#result').textContent=`Retrieval failed: ${e.message}`;}finally{button.disabled=false;}});
 }catch(e){$('#error').hidden=false;$('#error').textContent=e.message;}}
init();
