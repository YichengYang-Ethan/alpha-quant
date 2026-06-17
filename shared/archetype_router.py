#!/usr/bin/env python3
"""Archetype router for the 5+2 method.

Classify a company from its factsheet into 1 of 8 archetypes (or a universal
fallback) and return the per-step playbook (valuation method, financials focus,
moat lens, bull template, risk clusters). This is a FIRST-PASS heuristic — the
analyst refines it (a name can span archetypes; take the share-price main line).
Ported from references/5plus2/06-archetype-router.md.

  python shared/archetype_router.py NVDA          # factsheet -> archetype + playbook
"""
from __future__ import annotations
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from factsheet import build_factsheet  # noqa: E402

# 8 archetypes + universal fallback (the [TICKER] tags are examples, not hard rules)
ARCHETYPES = {
    "semis_leader": {
        "id": 1, "name": "Compute/semis leader (near-monopoly)", "examples": "NVDA, TSM",
        "moat_lens": "ecosystem/network effects + scale + capital + first-mover ('winner keeps winning'); share dip != bad if TAM grows",
        "financials": "gross margin = supply/demand thermometer (high = demand>supply); LT-debt/assets <40%; FCF; capex coverage for heavy assets",
        "valuation": "forward PE vs SPX/own history; DCF base/bull/bear",
        "bull": "selling-the-shovels / toll-booth certainty",
        "risks": "demand miss -> margin; competition (in-house/share); supply-chain/geo; product delay"},
    "platform": {
        "id": 2, "name": "Quality large-cap platform (profitable)", "examples": "MSFT, META, GOOGL, AMZN",
        "moat_lens": "network effects/ecosystem/full-stack distribution; split growth (AI vs non-AI)",
        "financials": "gross margin (software 80%+); FCF yield cross-tech; segment profit vs revenue (value != revenue driver)",
        "valuation": "forward PE (tell the re-rating history); complex conglomerate can be 'neither cheap nor expensive'; FCF",
        "bull": "certainty + optionality; investor management; can actively steer results",
        "risks": "regulation/antitrust; cyclical ads; capital-allocation overspend; customer concentration"},
    "saas_growth": {
        "id": 3, "name": "High-growth software / SaaS", "examples": "PLTR, SNOW, TEM",
        "moat_lens": "the one thing rivals structurally can't do (e.g. cross-cloud neutrality); switching cost/data gravity/vertical depth/data flywheel; NRR",
        "financials": "growth + is-it-accelerating; NRR>120%; GAAP loss -> strip SBC -> FCF margin; asset-light low capex; net cash (incl convertibles)",
        "valuation": "profitable -> forward PE (tolerate high); GAAP-loss/consumption -> EV/Sales + Meritech 20+20 + quality peer; pre-revenue -> P/S",
        "bull": "AI transition / scarce industry position; high ceiling, stable floor",
        "risks": "paradigm shift (AI agent bypasses the middle layer); competition; valuation premium; high SBC dilution (no buyback); key-man"},
    "story_option": {
        "id": 4, "name": "Story / faith / option stock", "examples": "TSLA",
        "moat_lens": "value-driver != revenue-driver (value sits in the unproven business)",
        "financials": "gross-margin trend; cash flow",
        "valuation": "NOT relative multiples -> SOTP-DCF (discount each segment, see where value concentrates)",
        "bull": "conditional bull ('only if you believe X commercializes')",
        "risks": "tech doesn't deliver; founder misjudgment/distraction; subsidy rollback; price > base"},
    "capital_intensive": {
        "id": 5, "name": "Capital-intensive / AI-infra / credit-sensitive", "examples": "ORCL",
        "moat_lens": "business-model innovation (capital decoupling / customers bring capacity) but margin-dilutive",
        "financials": "capex/revenue + net leverage = net-debt/EBITDA (>3 downgrade / ~4 speculative) + FCF turned negative by capex; watch rating agencies",
        "valuation": "forward PE two legs (EPS x multiple, proxy-stock sentiment); style-switch re-rating",
        "bull": "order/backlog visibility; proxy stock",
        "risks": "customer concentration; balance-sheet/capex spiral; AI-demand fragility"},
    "bank": {
        "id": 6, "name": "Bank / financials", "examples": "GS",
        "moat_lens": "integrated one-stop loop; brand/century relationships/capital barrier",
        "financials": "efficiency ratio = opex/revenue (lower better) + ROTCE + CET1 (gross-margin/leverage/FCF do NOT apply)",
        "valuation": "P/B x BPS (ROTCE-driven), NOT PE",
        "bull": "cyclical recovery + structural improvement",
        "risks": "strong-cyclical downturn (non-linear); private-credit systemic; regulatory capital"},
    "retail_defensive": {
        "id": 7, "name": "Retail / consumer defensive", "examples": "COST",
        "moat_lens": "membership flywheel / scale cost / brand; high turnover = pricing power",
        "financials": "gross margin may be deliberately low (membership ~11%, 'GM=moat' N/A) -> net margin stable + renewal 90%+ + comps + turnover",
        "valuation": "forward PE; expensive itself = the #1 risk",
        "bull": "defensive counter-cyclical compounder ('sleep well at night')",
        "risks": "valuation expensive (slow to digest + no downside protection); AI/innovation lag; weakening consumer"},
    "turnaround": {
        "id": 8, "name": "Distressed turnaround", "examples": "INTC",
        "moat_lens": "an old moat to be repaired + a new catalyst",
        "financials": "read the repair SLOPE/inflection (not absolute level); heavy assets -> volatile earnings",
        "valuation": "DCF + historical PE fail -> market-cap-space estimate (TAM x share x net-margin x PE + option value)",
        "bull": "turnaround (new CEO + catalyst + sector beta + expectations gap)",
        "risks": "pullback after a big run; yield/execution ramp; can the turnaround become systemic"},
    "fallback": {
        "id": 0, "name": "Universal fallback (biotech/REIT/insurance/industrial/shipping/utility/energy...)", "examples": "(anything not 1-8)",
        "moat_lens": "find the one thing rivals structurally can't do (neutrality/license/network/scale/switching/brand)",
        "financials": "base (growth + gross-margin trend + LT-debt/assets <40% + FCF+ + net margin) + ROIC; add industry-specific as needed",
        "valuation": "profitable -> forward PE; unprofitable -> EV/Sales or P/S; story -> SOTP; always DCF base/bull/bear, base anchored below analyst mean",
        "bull": "one-line bull + premise; prefer certainty > elasticity; disprove the popular bear first",
        "risks": "4 clusters: core-driver miss; competition/share loss; paradigm shift; valuation high (+ leadership/cyclical/regulatory as needed)"},
}


def classify(fs: dict) -> str:
    """First-pass heuristic from factsheet signals -> archetype key (analyst refines)."""
    ctx, q, g = fs.get("context", {}) or {}, fs.get("quality", {}) or {}, fs.get("growth", {}) or {}
    st = fs.get("statements", {}) or {}
    sector = (ctx.get("sector") or "").lower()
    industry = (ctx.get("industry") or "").lower()
    nm = q.get("net_margin_pct")
    rev_g = g.get("revenue_growth_pct")
    mcap = (fs.get("valuation", {}) or {}).get("market_cap") or 0
    unprofitable = nm is not None and nm < 0
    high_growth = rev_g is not None and rev_g > 30

    if "financ" in sector or any(k in industry for k in ("bank", "capital market", "insurance", "credit service")):
        return "bank"
    if "consumer defensive" in sector:  # COST/WMT-type; e-commerce (AMZN) is Consumer Cyclical -> platform
        return "retail_defensive"
    is_semi = any(k in industry for k in ("semiconductor", "semis"))
    is_software = any(k in industry for k in ("software", "saas", "information technology service", "infrastructure")) and "semiconductor" not in industry
    if is_semi:
        # low/negative-margin semis read as turnaround; healthy-margin as leader
        return "turnaround" if (unprofitable or (nm is not None and nm < 8)) else "semis_leader"
    # mega-cap, profitable, mature-growth platform (MSFT/GOOGL/META/AMZN/AAPL) — before SaaS;
    # gated to platform-y sectors so mega energy/industrials fall through to fallback
    if (mcap and mcap > 5e11 and not unprofitable and not high_growth
            and any(s in sector for s in ("technology", "communication", "consumer cyclical"))):
        return "platform"
    if is_software:
        return "saas_growth"
    if unprofitable:
        return "saas_growth" if high_growth else "turnaround"
    # smaller profitable tech/comm platform
    if ("technology" in sector or "communication" in sector) and mcap and mcap > 1e11:
        return "platform"
    return "fallback"


def route(ticker: str) -> dict:
    fs = build_factsheet(ticker)
    if fs.get("_err"):
        return {"ticker": ticker, "_err": fs["_err"]}
    key = classify(fs)
    pb = ARCHETYPES[key]
    return {"ticker": ticker, "archetype": key, "archetype_id": pb["id"], "archetype_name": pb["name"],
            "playbook": pb,
            "signals": {"sector": fs.get("context", {}).get("sector"),
                        "industry": fs.get("context", {}).get("industry"),
                        "net_margin_pct": fs.get("quality", {}).get("net_margin_pct"),
                        "revenue_growth_pct": fs.get("growth", {}).get("revenue_growth_pct"),
                        "market_cap": fs.get("valuation", {}).get("market_cap")},
            "note": "first-pass heuristic; analyst confirms (a name can span archetypes — take the share-price main line)"}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python archetype_router.py <TICKER>", file=sys.stderr); raise SystemExit(1)
    print(json.dumps(route(sys.argv[1]), ensure_ascii=False, indent=2))
