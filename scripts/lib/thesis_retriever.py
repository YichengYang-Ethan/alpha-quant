#!/usr/bin/env python3
"""Few-shot retriever over the local AP thesis corpus index (Tier-2 helper).

retrieve(query_text, sector=None, k=4, prefer_type='buy') -> list of exemplar
theses (ticker/type/date/outcome/title/md) most similar by theme + keyword
overlap, to inject as few-shot for the Quant-style analyzer.

Index is LOCAL ONLY (built by build_fewshot_index.py). Falls back gracefully if absent.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent   # repo root
INDEX = ROOT / "data/alpha_picks/fewshot_index.json"
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _helpers():
    from build_fewshot_index import classify, keywords  # noqa: E402
    return classify, keywords


def load_index():
    if not INDEX.exists():
        return []
    return json.load(open(INDEX))["records"]


def retrieve(query_text: str, sector: str | None = None, k: int = 4,
             prefer_type: str = "buy") -> list[dict]:
    recs = load_index()
    if not recs:
        return []
    classify, keywords = _helpers()
    q_theme = classify(query_text)
    q_kw = set(keywords(query_text, 20))
    scored = []
    for r in recs:
        kw_overlap = len(q_kw & set(r.get("keywords", [])))
        theme_match = 2.0 if r.get("theme") == q_theme and q_theme != "other" else 0.0
        sector_match = 1.0 if sector and r.get("sector") and sector == r.get("sector") else 0.0
        type_bonus = 0.5 if r.get("type") == prefer_type else 0.0
        score = theme_match + kw_overlap + sector_match + type_bonus
        scored.append((score, r))
    scored.sort(key=lambda x: -x[0])
    out = []
    for s, r in scored[:k]:
        out.append({"ticker": r["ticker"], "company": r.get("company"), "type": r["type"],
                    "date": r["date"], "theme": r["theme"], "outcome": r["outcome"],
                    "title": r["title"], "md": r["md"], "_score": round(s, 1)})
    return out


def format_fewshot(exemplars: list[dict]) -> str:
    """Render exemplars as a few-shot block for the analyzer prompt."""
    if not exemplars:
        return "(no corpus exemplars available)"
    parts = []
    for e in exemplars:
        parts.append(f"### Past Alpha Pick: {e['ticker']} ({e['date']}, {e['type']}, theme={e['theme']})\n"
                     f"Outcome: {e['outcome']}\n{e['md']}")
    return "\n\n---\n\n".join(parts)


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "AI data center optical networking semiconductor chips"
    ex = retrieve(q, k=5)
    print(f"query: {q!r}\nretrieved {len(ex)}:")
    for e in ex:
        print(f"  [{e['_score']}] {e['ticker']:6} {e['date']} {e['type']:4} {e['theme']:12} | {e['outcome']}")
        print(f"          {e['title'][:60]}")
