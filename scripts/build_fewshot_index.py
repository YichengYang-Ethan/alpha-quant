#!/usr/bin/env python3
"""Build the local few-shot retrieval index over the 147-thesis AP corpus.

For each thesis: theme tag + keywords + ledger outcome + trimmed markdown, so the
Tier-2 analyzer can retrieve K most-similar past AP theses as style/reasoning
exemplars. Output is LOCAL ONLY (gitignored) — contains provider-derived text.

Run: python scripts/build_fewshot_index.py
"""
import json, re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data/alpha_picks/exports/ap_corpus.jsonl"
OUT = ROOT / "data/alpha_picks/fewshot_index.json"   # gitignored

THEMES = {
    "ai_infra":      r"\bAI\b|data center|optical|networking|interconnect|hyperscaler|accelerat|GPU|inference",
    "semis":         r"semiconductor|\bchip|wafer|foundry|\bfab\b|lithograph|node\b|silicon",
    "metals_mats":   r"aluminum|zinc|copper|steel|\bmetal|mining|\bgold\b|silver|lithium|materials",
    "energy":        r"\boil\b|natural gas|refin|\benergy\b|\bcoal\b|drilling|\bLNG\b|upstream|midstream",
    "financials":    r"\bbank|broker|insur|lending|financial services|derivativ|\bFCM\b|payments|asset manage",
    "software_saas": r"software|\bSaaS\b|cloud|platform|subscription|\bARR\b|recurring revenue",
    "industrials":   r"industrial|infrastructure|construction|engineering|electrical|\bpower\b|grid|aerospace|defense",
    "consumer":      r"retail|consumer|\bbrand|restaurant|apparel|cruise|travel|e-commerce|footwear",
    "healthcare":    r"biotech|pharma|\bdrug\b|clinical|therap|medical|diagnostic|FDA",
}
STOP = set("the a an and or of to in for on with is are be as by at from this that its their our we "
           "company stock shares it has have was were will market price its also which than into "
           "alpha picks portfolio buy thesis business overview strong our".split())


def classify(text: str) -> str:
    t = text or ""
    best, bestn = "other", 0
    for theme, pat in THEMES.items():
        n = len(re.findall(pat, t, re.I))
        if n > bestn:
            best, bestn = theme, n
    return best


def keywords(text: str, k: int = 15) -> list[str]:
    toks = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", (text or "").lower())
    toks = [w for w in toks if w not in STOP]
    return [w for w, _ in Counter(toks).most_common(k)]


def outcome_str(led: dict | None) -> str:
    if not led:
        return "no ledger match"
    tr = led.get("total_return")
    pt = led.get("pick_type"); act = led.get("active")
    state = "still held" if act else "closed"
    if tr is None:
        return f"{state}, {pt or 'standard'} (return n/a)"
    verdict = "WORKED" if tr > 15 else "ok" if tr > 0 else "LOST"
    return f"{state}, {pt or 'standard'}, return {tr:+.0f}% [{verdict}]"


def main():
    recs = [json.loads(l) for l in open(CORPUS) if l.strip()]
    index = []
    for r in recs:
        body = (r.get("title", "") + " " + " ".join(r.get("summary", [])) + " " + (r.get("text") or "")[:2000])
        md = r.get("markdown") or ""
        index.append({
            "id": r["id"], "ticker": r.get("ticker"), "company": r.get("company"),
            "type": r.get("type"), "date": r.get("date"), "sector": r.get("sector"),
            "theme": classify(body),
            "keywords": keywords(body),
            "title": r.get("title"), "summary": r.get("summary", []),
            "outcome": outcome_str(r.get("ledger")),
            "md": md[:3500],   # trimmed exemplar for few-shot injection
        })
    json.dump({"n": len(index), "source": "thesis corpus — LOCAL ONLY",
               "records": index}, open(OUT, "w"), ensure_ascii=False)
    from collections import Counter as C
    print(f"wrote {OUT} ({len(index)} theses)")
    print("themes:", dict(C(r["theme"] for r in index)))
    print("types:", dict(C(r["type"] for r in index)))


if __name__ == "__main__":
    main()
