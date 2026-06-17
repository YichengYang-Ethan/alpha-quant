#!/usr/bin/env python3
"""Tier-2 atom: assemble the full data package for a Quant-style thesis on ONE ticker.

This does NOT call an LLM. It gathers the deterministic inputs — real provider factor
scores (gate), the meitou factsheet (fundamentals/valuation/technicals/news),
K few-shot exemplars from the AP corpus (+ their realized outcomes), and the
ledger/honesty context — into a package the /alpha-quant skill (or the workflow's
Tier-2 subagent) turns into the thesis card. Same logic on both paths.

CLI:  python shared/alpha_analyze.py FN --source sa [--json]
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "shared"))
from lib.universe_scores import get_universe_scores, gate_strong_buy, FACTORS  # noqa: E402
from lib.thesis_retriever import retrieve, format_fewshot                       # noqa: E402

FACTSHEET = str(ROOT / "shared" / "factsheet.py")   # portable yfinance adapter, in-repo (no external dependency)
VENV = "/Users/ethanyang/clawd/.venv/bin/python"
LEDGER = ROOT / "data/alpha_picks/ap_ledger_2026-06-16.json"
HOLDINGS = ROOT / "data/alpha_picks/ap_holdings_2026-06-16.json"

# Honesty layer — AP-native (109-pick ledger) + event study. NOT a "will go up" signal.
HONESTY = ("Single-name top-rated ≈ coin-flip: the pick portfolio's closed-standard median +2.9%, "
           "median alpha −16%, only ~30% beat SPY. The +434% is portfolio compounding from "
           "a few multi-baggers held for years + ruthless cut-losers discipline. Regime-dependent "
           "(momentum/revisions engine; weak in 2023-24, strong in 2025-26). This card is a "
           "FILTER + framework, not a buy signal.")


def factsheet(ticker: str) -> dict:
    try:
        out = subprocess.run([VENV, FACTSHEET, ticker, "--json"], capture_output=True, text=True, timeout=120)
        # factsheet prints JSON; grab the first {...} block
        s = out.stdout
        i, j = s.find("{"), s.rfind("}")
        return json.loads(s[i:j+1]) if i >= 0 else {"_err": "no json", "_stderr": out.stderr[:200]}
    except Exception as e:
        return {"_err": str(e)}


def ledger_context(ticker: str) -> dict:
    led = json.load(open(LEDGER))["picks"] if LEDGER.exists() else []
    mine = [p for p in led if (p.get("ticker") or "").upper() == ticker.upper()]
    hold = json.load(open(HOLDINGS))["holdings"] if HOLDINGS.exists() else []
    held = next((h for h in hold if h["ticker"].upper() == ticker.upper()), None)
    return {"is_ap_pick": bool(mine), "n_picks": len(mine),
            "history": [{k: p.get(k) for k in ("created_at","removed_at","buy_price","total_return","pick_type","active")} for p in mine],
            "currently_held": held}


def analyze(ticker: str, source: str = "sa") -> dict:
    ticker = ticker.upper()
    uni = get_universe_scores(source)
    if ticker not in uni.index:
        scores = {"_note": f"{ticker} not in {source} universe"}
        gated = False
    else:
        r = uni.loc[ticker]
        scores = {"quant": round(float(r["quant"]), 2), "label": r["label"],
                  **{f: r[f] for f in FACTORS}, "rank_pct": round(float(r["rank_pct"]), 4)}
        gated = ticker in gate_strong_buy(uni).index
    fs = factsheet(ticker)
    ctx = (fs.get("context") or {})
    sector = ctx.get("sector")
    query = " ".join(filter(None, [ctx.get("name"), sector, ctx.get("industry"),
                                    " ".join(n.get("title","") for n in (ctx.get("recent_news") or [])[:3])]))
    exemplars = retrieve(query or ticker, sector=sector, k=4)
    return {
        "ticker": ticker, "source": source, "asof": uni.attrs.get("asof"),
        "gate": {"strong_buy_and_floor": gated, "scores": scores},
        "factsheet": fs,
        "fewshot": exemplars,
        "ledger_context": ledger_context(ticker),
        "honesty": HONESTY,
    }


def brief(pkg: dict) -> str:
    g = pkg["gate"]; s = g["scores"]
    lines = [f"=== Quant data package · {pkg['ticker']} (source={pkg['source']}, asof={pkg['asof']}) ===",
             f"GATE: {'✅ PASS (Strong Buy + floor)' if g['strong_buy_and_floor'] else '⛔ FAIL / not SB'}",
             f"  quant={s.get('quant')} {s.get('label')} | V{s.get('V')} G{s.get('G')} P{s.get('P')} M{s.get('M')} R{s.get('R')} | rank_pct={s.get('rank_pct')}"]
    fs = pkg["factsheet"]; v = fs.get("valuation", {}); q = fs.get("quality", {}); gr = fs.get("growth", {})
    if not fs.get("_err"):
        lines += [f"  fwdPE={v.get('forward_pe')} PEG={v.get('peg')} | rev_growth={gr.get('revenue_growth_pct')}% "
                  f"gross_m={q.get('gross_margin_pct')}% net_m={q.get('net_margin_pct')}% | sector={(fs.get('context') or {}).get('sector')}"]
    lc = pkg["ledger_context"]
    lines.append(f"  AP pick history: {'yes ('+str(lc['n_picks'])+')' if lc['is_ap_pick'] else 'no'}"
                 + (f" | currently held {lc['currently_held']['return_pct']}%" if lc.get('currently_held') else ""))
    lines.append(f"\nFEW-SHOT exemplars ({len(pkg['fewshot'])}):")
    for e in pkg["fewshot"]:
        lines.append(f"  • {e['ticker']} ({e['date']}, {e['theme']}) — {e['outcome']}")
    lines.append(f"\nHONESTY: {pkg['honesty']}")
    return "\n".join(lines)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    src = "sa"
    if "--source" in sys.argv:
        src = sys.argv[sys.argv.index("--source") + 1]
    tk = args[0] if args else "FN"
    pkg = analyze(tk, src)
    if "--json" in sys.argv:
        print(json.dumps(pkg, ensure_ascii=False, indent=2, default=str))
    else:
        print(brief(pkg))
