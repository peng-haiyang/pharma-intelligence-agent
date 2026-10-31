// Genuine lexical retrieval over the approved snapshot; no model or gold-answer lookup.
export const ENGINE = 'snapshot-bm25-v1';
const STOP = new Set('a an the what which why how does do is are can be to of and or for in on with as from by this that it have has according overview describe describes japan japanese public please tell me about'.split(' '));
export function tokens(text) {
  const normalized=text.normalize('NFKC').toLowerCase();
  const words=(normalized.match(/[a-z0-9]+/g)||[]).filter(w=>!STOP.has(w)&&w.length>1).map(w=>w.length>4?w.replace(/s$/,''):w);
  for(const segment of normalized.match(/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}ー]+/gu)||[])
    for(let i=0;i<segment.length-1;i++) words.push(segment.slice(i,i+2));
  return words;
}
const RULES=[
 ['instruction_override',/ignore|invent|fabricat|make up|system prompt|無視|作って|捏造/i],
 ['individual_medical_advice',/\b(i|my|me)\b.{0,45}\b(take|dose|prescri|symptom)|\bdosage\b|私は|今夜|何mg|処方して/i],
 ['unsupported_current_data',/\btoday\b|\bcurrent\b|\blatest\b|\b203\d\b|\bforecast\b|\brevenue\b|\bnhi\b|\bprice\b|今日|最新|現在|売上|薬価|予測/i],
 ['unsupported_causality',/\bprove\b|\bcaus(?:e|ed|al|ality)\b|因果|証明/i],
];
export function scopeReason(question){return RULES.find(([,re])=>re.test(question))?.[0]??null;}
export function rank(question, docs, limit=3){
  const q=[...new Set(tokens(question))];
  const bags=docs.map(d=>tokens(d.passage));
  const avg=bags.reduce((s,b)=>s+b.length,0)/bags.length;
  const scored=docs.map((doc,i)=>{
    const bag=bags[i], counts=new Map();for(const t of bag)counts.set(t,(counts.get(t)||0)+1);
    let score=0,overlap=0;
    for(const t of q){const tf=counts.get(t)||0;if(!tf)continue;overlap++;
      const df=bags.filter(b=>b.includes(t)).length;
      score+=Math.log(1+(docs.length-df+.5)/(df+.5))*(tf*2.2)/(tf+1.2*(.25+.75*bag.length/avg));
    }
    return {doc,score,overlap};
  });
  // Conservative lexical gate, deliberately independent of benchmark questions/labels.
  const japanese=/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}]/u.test(question);
  return scored.filter(s=>s.overlap>=(japanese?3:2)&&s.score>=1).sort((a,b)=>b.score-a.score||a.doc.id.localeCompare(b.doc.id)).slice(0,limit);
}
export async function verify(doc){
  if(!doc||typeof doc.source_text!=='string'||!/^[a-f0-9]{64}$/.test(doc.sha256))return false;
  const hosts={PMDA:'www.pmda.go.jp',MHLW:'www.mhlw.go.jp',JRS:'www.jrs.or.jp'};
  let url;try{url=new URL(doc.url);}catch{return false;}
  if(url.protocol!=='https:'||url.host!==hosts[doc.publisher]||url.pathname==='/'||url.hash||url.username||url.password)return false;
  const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(doc.source_text));
  const hash=[...new Uint8Array(bytes)].map(x=>x.toString(16).padStart(2,'0')).join('');
  // Corpus passages normalize whitespace; verify this too before showing a citation.
  return hash===doc.sha256&&doc.passage===doc.source_text.replace(/\s+/gu,' ').trim();
}
export function citation(doc,score){
  const {source_text,display,file,...safe}=doc;return {...safe,lexical_score:Number(score.toFixed(4))};
}
export async function investigate(question,docs,emit=()=>{}){
  const started=performance.now();let seq=0;
  const event=(step,status,detail)=>emit({sequence:++seq,step,status,detail,elapsed_ms:Math.round((performance.now()-started)*100)/100});
  event('request','complete','Question accepted. No question storage or external model call.');
  event('scope','running','Checking the limits of this public snapshot.');
  const reason=scopeReason(question);
  if(reason){event('scope','blocked',reason);event('result','complete','Abstained: this request cannot be supported by the snapshot.');return {status:'insufficient_evidence',reason,citations:[],answer:null,engine:ENGINE};}
  event('scope','complete','No configured exclusion matched; this is not a guarantee of safety or completeness.');
  event('search','running',`Searching ${docs.length} approved public summaries with bilingual lexical matching.`);
  const hits=rank(question,docs);event('search','complete',`${hits.length} candidate source(s) passed the lexical threshold.`);
  event('provenance','running','Verifying content hashes, passages and approved publisher URLs. Not checking live publisher pages.');
  const checked=await Promise.all(hits.map(async h=>({h,valid:await verify(h.doc)})));
  if(checked.some(c=>!c.valid)){event('provenance','failed','A source failed integrity checks. No evidence will be returned.');event('result','failed','Evidence unavailable.');return {status:'unavailable',reason:'source_integrity_failed',citations:[],answer:null,engine:ENGINE};}
  event('provenance','complete',`${checked.length} candidate source(s) matched the approved snapshot.`);
  const citations=checked.map(({h})=>citation(h.doc,h.score));
  event('result','complete',citations.length?'Evidence passages ready. No generated answer or clinical recommendation.':'Abstained: no evidence passed the lexical threshold.');
  return {status:citations.length?'retrieved':'insufficient_evidence',reason:citations.length?'snapshot_evidence_only':'no_lexical_match',citations,answer:null,engine:ENGINE};
}
