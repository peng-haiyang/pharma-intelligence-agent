"""Small, auditable evidence baseline. Public information only."""
from dataclasses import dataclass
import re
from collections import Counter
from math import sqrt

@dataclass(frozen=True)
class Evidence:
    id: str
    title: str
    text: str
    url: str
    published: str

EVIDENCE = [
    Evidence("mhlw-shingles", "MHLW shingles routine vaccination",
             "Japan's routine shingles vaccination programme includes people aged 65 and transitional age cohorts during fiscal years 2025 to 2029. Municipal eligibility, co-payment and delivery capacity require local assessment.",
             "https://www.mhlw.go.jp/", "baseline-2026-10-13"),
    Evidence("gsk-relvar", "GSK Japan Relvar approval history",
             "GSK Japan's 24 June 2024 release discusses paediatric approvals and notes earlier adult asthma approval in September 2013 and COPD approval in December 2016. Approval history does not establish generic launch timing.",
             "https://jp.gsk.com/", "2024-06-24"),
    Evidence("mhlw-prices", "MHLW NHI drug price information",
             "Japan's MHLW drug price listing announced an update effective 14 October 2026. A list update alone does not prove that a particular competitor has entered the market.",
             "https://www.mhlw.go.jp/", "baseline-2026-10-13"),
    Evidence("respiratory-guidelines", "Japan respiratory guideline watch",
             "Japanese respiratory professional societies list 2026 asthma and COPD guideline editions. Medical review of authorised full guideline texts is required before drawing treatment-positioning conclusions.",
             "https://www.jrs.or.jp/", "baseline-2026-10-13"),
]

STOPWORDS = {"what", "are", "the", "for", "and", "with", "from", "about", "into",
             "this", "that", "have", "does", "japan", "latest", "commercial",
             "market", "information", "our", "could", "would", "should", "how"}

def tokens(value: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+|[\u3040-\u30ff\u3400-\u9fff]+", value.lower())
            if len(w) > 2 and w not in STOPWORDS]

def retrieve(question: str, limit: int = 3) -> list[dict]:
    """Transparent cosine-like term-frequency retrieval; no LLM and no embeddings yet."""
    q = Counter(tokens(question))
    if not q:
        return []
    scored = []
    for item in EVIDENCE:
        terms = Counter(tokens(item.title + " " + item.text))
        overlap = sum(q[t] * terms[t] for t in q)
        denom = sqrt(sum(v*v for v in q.values()) * sum(v*v for v in terms.values()))
        score = overlap / denom if denom else 0
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: (-x[0], x[1].id))
    return [{"id": e.id, "title": e.title, "passage": e.text,
             "url": e.url, "published": e.published, "score": round(score, 4)}
            for score, e in scored[:limit]]
