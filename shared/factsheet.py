#!/usr/bin/env python3
"""factsheet.py — standalone data adapter for the 5+2 skill (English / portable).

Given a ticker, pulls every "hard number" the 5+2 method needs and assembles a
structured factsheet. Depends ONLY on `yfinance` (pip install yfinance) — no
proprietary data layer, so it runs on any machine.

Design (borrowed from virattt/ai-hedge-fund):
  - This script only collects *quantifiable facts*; it makes no subjective calls.
  - The qualitative judgement (industry/moat narrative/management) is left to the
    persona LLM in SKILL.md.

Usage:
    python factsheet.py NVDA            # human-readable factsheet
    python factsheet.py NVDA --json     # structured JSON (for the skill to consume)

Requires: pip install yfinance   (pulls in pandas/numpy automatically)
"""
from __future__ import annotations

import json
import math
import sys

# Constants for the simple DCF/WACC (transparent, override if you like)
EQUITY_RISK_PREMIUM = 0.05   # ~5% long-run equity risk premium
COST_OF_DEBT = 0.045         # pre-tax cost of debt assumption
TAX_RATE_DEFAULT = 0.21      # US statutory-ish default
TERMINAL_GROWTH = 0.025      # perpetuity growth in the reverse DCF
DCF_YEARS = 5                # explicit horizon for the reverse DCF


# --- small helpers ----------------------------------------------------------
def _f(v, default=None):
    """Safe float; NaN/None -> default."""
    try:
        x = float(v)
        return x if math.isfinite(x) else default
    except (TypeError, ValueError):
        return default


def _pct(v, ndigits=2):
    """Fraction -> percent number, e.g. 0.153 -> 15.3."""
    x = _f(v)
    return round(x * 100, ndigits) if x is not None else None


def _round_floats(obj, ndigits=4):
    if isinstance(obj, float):
        return round(obj, ndigits) if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _round_floats(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_floats(v, ndigits) for v in obj]
    return obj


def _row(df, *names):
    """First matching row of a yfinance statement DataFrame as a Series, else None."""
    if df is None or getattr(df, "empty", True):
        return None
    for n in names:
        if n in df.index:
            return df.loc[n]
    return None


def _latest(series):
    """First finite value of a statement Series (statements are newest-first)."""
    if series is None:
        return None
    for v in series:
        fv = _f(v)
        if fv is not None:
            return fv
    return None


# --- risk-free rate (10y treasury via ^TNX) ---------------------------------
def _risk_free_rate(default=0.045) -> float:
    try:
        import yfinance as yf
        h = yf.Ticker("^TNX").history(period="5d")
        if h is not None and not h.empty:
            return round(float(h["Close"].dropna().iloc[-1]) / 100.0, 4)
    except Exception:
        pass
    return default


# --- technicals (timing) -----------------------------------------------------
def _rsi(close, period: int = 14):
    delta = close.diff().dropna()
    if len(delta) < period + 1:
        return None
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 1)


def _technicals(t) -> dict:
    try:
        hist = t.history(period="1y")
    except Exception:
        return {}
    if hist is None or getattr(hist, "empty", True) or "Close" not in hist:
        return {}
    close = hist["Close"].dropna()
    if close.empty:
        return {}
    last = float(close.iloc[-1])
    ma50 = float(close.tail(50).mean()) if len(close) >= 50 else None
    ma200 = float(close.tail(200).mean()) if len(close) >= 200 else None
    hi52, lo52 = float(close.max()), float(close.min())
    mdd = float((close / close.cummax() - 1).min()) * 100
    return {
        "price": round(last, 2),
        "ma50": round(ma50, 2) if ma50 else None,
        "ma200": round(ma200, 2) if ma200 else None,
        "above_ma50": (last > ma50) if ma50 else None,
        "above_ma200": (last > ma200) if ma200 else None,
        "rsi14": _rsi(close),
        "ret_1y_pct": round((last / float(close.iloc[0]) - 1) * 100, 1),
        "max_drawdown_1y_pct": round(mdd, 1),
        "pct_from_52w_high": round((last / hi52 - 1) * 100, 1),
        "pct_above_52w_low": round((last / lo52 - 1) * 100, 1),
        "range_52w": [round(lo52, 2), round(hi52, 2)],
    }


# --- WACC (simple CAPM) ------------------------------------------------------
def _wacc(beta, rf, mktcap, total_debt):
    beta = _f(beta)
    if beta is None or mktcap is None:
        return None
    ke = rf + beta * EQUITY_RISK_PREMIUM
    e = mktcap
    d = total_debt or 0.0
    v = e + d
    if v <= 0:
        return None
    kd_after_tax = COST_OF_DEBT * (1 - TAX_RATE_DEFAULT)
    return round((e / v) * ke + (d / v) * kd_after_tax, 4)


# --- reverse DCF: what FCF growth is the price implying? --------------------
def _pv_given_growth(fcf, w, g, tg, years):
    pv, f = 0.0, fcf
    for yr in range(1, years + 1):
        f = f * (1 + g)
        pv += f / (1 + w) ** yr
    if w <= tg:
        return None
    tv = f * (1 + tg) / (w - tg)
    pv += tv / (1 + w) ** years
    return pv


def _implied_growth(ev, fcf, w, tg, years=DCF_YEARS):
    """Solve growth g such that PV(FCF) == EV. Bisection. None if infeasible."""
    if not (ev and fcf and w) or fcf <= 0 or w <= tg:
        return None
    lo, hi = -0.5, 1.0
    pv_lo = _pv_given_growth(fcf, w, lo, tg, years)
    pv_hi = _pv_given_growth(fcf, w, hi, tg, years)
    if pv_lo is None or pv_hi is None or not (min(pv_lo, pv_hi) <= ev <= max(pv_lo, pv_hi)):
        return None
    for _ in range(60):
        mid = (lo + hi) / 2
        pv = _pv_given_growth(fcf, w, mid, tg, years)
        if pv is None:
            return None
        if pv > ev:
            hi = mid
        else:
            lo = mid
    return round((lo + hi) / 2, 4)


def _reverse_dcf(ev, fcf, w):
    if w is None:
        return None
    grid = []
    for tg in (0.02, 0.025, 0.03):
        g = _implied_growth(ev, fcf, w, tg)
        if g is not None:
            grid.append(g)
    if not grid:
        return None
    center = round(sorted(grid)[len(grid) // 2], 4)
    spread = round((max(grid) - min(grid)) * 100, 1)
    return {"center": center, "spread_pp": spread,
            "verdict": "robust" if spread < 5 else "wide"}


# --- analyst target asymmetry ------------------------------------------------
def _asymmetry(price, low, mean, high):
    price, low, mean, high = _f(price), _f(low), _f(mean), _f(high)
    if not all(v is not None for v in (price, low, mean, high)) or price <= 0:
        return None
    up = high / price - 1
    down = low / price - 1
    return {
        "low": low, "mean": mean, "high": high,
        "up_pct": round(up, 4), "down_pct": round(down, 4),
        "asymmetry": round(abs(up / down), 2) if down else None,
    }


# --- ROIC (NOPAT / invested capital) from statements ------------------------
def _moat(t, info, revenue):
    try:
        inc = t.income_stmt
        bs = t.balance_sheet
    except Exception:
        return {}
    ebit = _latest(_row(inc, "EBIT", "Operating Income"))
    pretax = _latest(_row(inc, "Pretax Income"))
    tax = _latest(_row(inc, "Tax Provision"))
    tax_rate = (tax / pretax) if (pretax and tax is not None and pretax != 0) else TAX_RATE_DEFAULT
    tax_rate = min(max(tax_rate, 0.0), 0.5)
    if ebit is None:
        return {}
    nopat = ebit * (1 - tax_rate)
    ic = _latest(_row(bs, "Invested Capital"))
    if ic is None:
        debt = _latest(_row(bs, "Total Debt")) or 0.0
        equity = _latest(_row(bs, "Stockholders Equity", "Common Stock Equity")) or 0.0
        ic = debt + equity
    if not ic or ic <= 0:
        return {}
    roic = nopat / ic
    return {
        "roic": round(roic, 4),
        "margin": round(nopat / revenue, 4) if revenue else None,
        "turnover": round(revenue / ic, 4) if revenue else None,
        "moat_type": None,  # qualitative -> left to the LLM
    }


# --- statement-derived signals the method cares about most ------------------
def _statements(t) -> dict:
    """Debt/Total Assets using TOTAL debt incl. capital leases (Buffett <40%; this matches
    how the method reads e.g. AMZN's "~20%" — bond-only understates lease-heavy names),
    gross-margin trend (the single most important NVDA signal), SBC/revenue (SaaS dilution)."""
    out = {"debt_to_assets_pct": None, "debt_to_assets_trend": [],
           "lt_debt_only_to_assets_pct": None,
           "gross_margin_trend_q": [], "sbc_pct_revenue": None}
    # Debt / Total Assets — total debt incl. capital leases, by year
    try:
        b = t.balance_sheet
        ta = _row(b, "Total Assets")
        td = _row(b, "Total Debt", "Long Term Debt And Capital Lease Obligation")
        if ta is not None and td is not None:
            trend = []
            for c in b.columns:
                a_, d_ = _f(ta.get(c)), _f(td.get(c))
                if a_ and d_ is not None:
                    trend.append({"period": str(c.date()), "pct": round(d_ / a_ * 100, 1)})
            out["debt_to_assets_trend"] = trend
            if trend:
                out["debt_to_assets_pct"] = trend[0]["pct"]
        ltd = _row(b, "Long Term Debt")  # bonds only, for transparency
        if ta is not None and ltd is not None:
            a0, l0 = _f(ta.iloc[0]), _f(ltd.iloc[0])
            if a0 and l0 is not None:
                out["lt_debt_only_to_assets_pct"] = round(l0 / a0 * 100, 1)
    except Exception:
        pass
    # quarterly gross-margin trend (last 5 quarters, newest-first)
    try:
        q = t.quarterly_income_stmt
        rev, gp = _row(q, "Total Revenue"), _row(q, "Gross Profit")
        if rev is not None and gp is not None:
            tr = []
            for c in q.columns:
                r_, g_ = _f(rev.get(c)), _f(gp.get(c))
                if r_ and g_ is not None:
                    tr.append({"q": str(c.date()), "gm_pct": round(g_ / r_ * 100, 1)})
            out["gross_margin_trend_q"] = tr[:5]
    except Exception:
        pass
    # SBC / revenue (latest fiscal year)
    try:
        sbc = _latest(_row(t.cashflow, "Stock Based Compensation"))
        rev = _latest(_row(t.income_stmt, "Total Revenue"))
        if sbc is not None and rev:
            out["sbc_pct_revenue"] = round(sbc / rev * 100, 1)
    except Exception:
        pass
    return out


# --- context (industry / catalysts) -----------------------------------------
def _context(t, info) -> dict:
    news = []
    try:
        for n in (t.news or [])[:5]:
            c = n.get("content", n) if isinstance(n, dict) else {}
            title = c.get("title") or n.get("title")
            pub = (c.get("provider") or {}).get("displayName") if isinstance(c.get("provider"), dict) else n.get("publisher")
            date = c.get("pubDate") or c.get("displayTime")
            if title:
                news.append({"title": title, "publisher": pub,
                             "date": (str(date)[:10] if date else None)})
    except Exception:
        news = []
    nxt = None
    try:
        cal = t.calendar
        if isinstance(cal, dict):
            ed = cal.get("Earnings Date")
            if ed:
                nxt = str(ed[0] if isinstance(ed, (list, tuple)) else ed)[:10]
    except Exception:
        nxt = None
    return {
        "name": info.get("longName") or info.get("shortName") or "",
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "next_earnings": nxt,
        "recent_news": news,
    }


# --- assemble ----------------------------------------------------------------
def build_factsheet(ticker: str) -> dict:
    import yfinance as yf
    ticker = ticker.strip().upper()
    t = yf.Ticker(ticker)
    try:
        info = t.info or {}
    except Exception:
        info = {}

    rf = _risk_free_rate()
    price = _f(info.get("currentPrice")) or _f(info.get("regularMarketPrice"))
    mktcap = _f(info.get("marketCap"))
    ev = _f(info.get("enterpriseValue"))
    beta = _f(info.get("beta"))
    total_debt = _f(info.get("totalDebt"))
    total_cash = _f(info.get("totalCash"))
    fcf = _f(info.get("freeCashflow"))
    revenue = _f(info.get("totalRevenue"))
    ebit_ttm = _f(info.get("ebitda"))  # crude EV/EBIT fallback uses ebitda if needed
    ev_eff = ev or ((mktcap + (total_debt or 0) - (total_cash or 0)) if mktcap else None)
    wacc = _wacc(beta, rf, mktcap, total_debt)

    valuation = {
        "price": price,
        "market_cap": mktcap,
        "enterprise_value": ev_eff,
        "trailing_pe": _f(info.get("trailingPE")),
        "forward_pe": _f(info.get("forwardPE")),
        "peg": _f(info.get("pegRatio") or info.get("trailingPegRatio")),
        "price_to_book": _f(info.get("priceToBook")),
        "price_to_sales": _f(info.get("priceToSalesTrailing12Months")),
        "ev_to_sales": (ev_eff / revenue) if (ev_eff and revenue) else None,
        "wacc_pct": round(wacc * 100, 2) if wacc else None,
        "reverse_dcf_implied_growth": _reverse_dcf(ev_eff, fcf, wacc),
        "analyst_target_asymmetry": _asymmetry(
            price, info.get("targetLowPrice"), info.get("targetMeanPrice"),
            info.get("targetHighPrice")),
        "analyst_recommendation": info.get("recommendationKey"),
    }
    quality = {
        "gross_margin_pct": _pct(info.get("grossMargins")),
        "operating_margin_pct": _pct(info.get("operatingMargins")),
        "net_margin_pct": _pct(info.get("profitMargins")),
        "roe_pct": _pct(info.get("returnOnEquity")),
        "roa_pct": _pct(info.get("returnOnAssets")),
        "fcf_ttm": fcf,
        "fcf_margin_pct": round(fcf / revenue * 100, 1) if (fcf and revenue) else None,
        "debt_to_equity": _f(info.get("debtToEquity")),
        "total_cash": total_cash,
        "total_debt": total_debt,
        "net_cash": ((total_cash or 0) - (total_debt or 0)) if (total_cash or total_debt) else None,
    }
    growth = {
        "revenue_ttm": revenue,
        "revenue_growth_pct": _pct(info.get("revenueGrowth")),
        "earnings_growth_pct": _pct(info.get("earningsGrowth")),
    }
    fs = {"ticker": ticker}
    fs["context"] = _context(t, info)
    fs["valuation"] = valuation
    fs["quality"] = quality
    fs["growth"] = growth
    fs["moat"] = _moat(t, info, revenue)
    fs["statements"] = _statements(t)
    fs["technicals"] = _technicals(t)
    fs["beta"] = beta
    fs["risk_free_rate_pct"] = round(rf * 100, 2)
    return _round_floats(fs)


# --- pretty printer ----------------------------------------------------------
def _line(label, val, suffix=""):
    return f"  {label:<28} {val if val is not None else '—'}{suffix}"


def format_factsheet(fs: dict) -> str:
    c, v, q = fs.get("context", {}), fs.get("valuation", {}), fs.get("quality", {})
    g, m, s, t = fs.get("growth", {}), fs.get("moat", {}), fs.get("statements", {}), fs.get("technicals", {})
    L = ["\n" + "=" * 64, f"  {fs['ticker']}  {c.get('name', '')}",
         f"  {c.get('sector', '')} / {c.get('industry', '')}", "=" * 64]
    L.append("[ Valuation ]")
    L.append(_line("Price", v.get("price")))
    L.append(_line("Market Cap", v.get("market_cap")))
    L.append(_line("Trailing P/E", v.get("trailing_pe")))
    L.append(_line("Forward P/E", v.get("forward_pe")))
    L.append(_line("PEG", v.get("peg")))
    L.append(_line("P/B", v.get("price_to_book")))
    L.append(_line("P/S", v.get("price_to_sales")))
    L.append(_line("EV/Sales", v.get("ev_to_sales")))
    L.append(_line("WACC", v.get("wacc_pct"), "%"))
    rd = v.get("reverse_dcf_implied_growth")
    if rd:
        L.append(_line("Reverse-DCF implied growth", f"{_pct(rd.get('center'))}% ({rd.get('verdict')})"))
    asym = v.get("analyst_target_asymmetry")
    if asym:
        L.append(_line("Analyst target (L/M/H)", f"{asym.get('low')}/{asym.get('mean')}/{asym.get('high')} (asym {asym.get('asymmetry')})"))
    L.append(_line("Analyst rating", v.get("analyst_recommendation")))
    L.append("[ Quality ]")
    L.append(_line("Gross margin", q.get("gross_margin_pct"), "%"))
    L.append(_line("Operating margin", q.get("operating_margin_pct"), "%"))
    L.append(_line("Net margin", q.get("net_margin_pct"), "%"))
    L.append(_line("ROE", q.get("roe_pct"), "%"))
    L.append(_line("FCF margin", q.get("fcf_margin_pct"), "%"))
    L.append(_line("Net cash", q.get("net_cash")))
    L.append("[ Financial-health trend ]")
    L.append(_line("Debt / Total Assets (incl. leases)", s.get("debt_to_assets_pct"), "%  (Buffett <40%)"))
    if s.get("lt_debt_only_to_assets_pct") is not None:
        L.append(_line("  of which bonds only", s.get("lt_debt_only_to_assets_pct"), "%"))
    gmt = s.get("gross_margin_trend_q") or []
    if gmt:
        L.append(_line("Gross-margin trend (5q)", " -> ".join(f"{x['gm_pct']}%" for x in reversed(gmt))))
    L.append(_line("SBC / revenue", s.get("sbc_pct_revenue"), "%  (SaaS dilution)"))
    L.append("[ Moat (ROIC) ]")
    L.append(_line("ROIC", _pct(m.get("roic")), "%"))
    L.append(_line("NOPAT margin", _pct(m.get("margin")), "%"))
    L.append(_line("Capital turnover", m.get("turnover")))
    L.append("[ Growth ]")
    L.append(_line("Revenue growth YoY", g.get("revenue_growth_pct"), "%"))
    L.append(_line("Earnings growth YoY", g.get("earnings_growth_pct"), "%"))
    L.append("[ Technicals / timing ]")
    L.append(_line("RSI14", t.get("rsi14")))
    L.append(_line("Above MA50 / MA200", f"{t.get('above_ma50')} / {t.get('above_ma200')}"))
    L.append(_line("1y return", t.get("ret_1y_pct"), "%"))
    L.append(_line("From 52w high", t.get("pct_from_52w_high"), "%"))
    L.append(_line("Max drawdown 1y", t.get("max_drawdown_1y_pct"), "%"))
    L.append("[ Catalysts ]")
    L.append(_line("Next earnings", c.get("next_earnings")))
    for n in c.get("recent_news", [])[:5]:
        L.append(f"  - [{n.get('date', '')}] {n.get('title', '')}")
    L.append("=" * 64)
    return "\n".join(L)


def main(argv):
    if not argv:
        print("usage: python factsheet.py <TICKER> [--json]", file=sys.stderr)
        return 1
    fs = build_factsheet(argv[0])
    if "--json" in argv:
        print(json.dumps(fs, ensure_ascii=False, indent=2))
    else:
        print(format_factsheet(fs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
