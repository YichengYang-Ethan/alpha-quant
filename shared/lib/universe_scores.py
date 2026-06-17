#!/usr/bin/env python3
"""Data-source abstraction for the Quant factor screen (Tier 0-1).

get_universe_scores(source) returns ONE normalized table the downstream skill +
workflow consume, regardless of where the factor scores come from:

  source="sa"      -> local premium-provider ratings cache (max fidelity; needs a refresh)
                      reads ~/clawd/scripts/data/sa_quant_ratings.json (4.3k tickers)
  source="replica" -> portable yfinance screen (public-runnable, no paywall)
                      calls the alpha engine run_screen() (NDX100 + holdings)

Normalized columns: quant(1-5), label, V/G/P/M/R(letter), rank_pct(0-1, 1=best),
sector, source. Plus helpers: gate_strong_buy(), letter<->num.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import pandas as pd

SA_CACHE = Path("/Users/ethanyang/clawd/scripts/data/sa_quant_ratings.json")
CLAWD_SCRIPTS = "/Users/ethanyang/clawd/scripts"

# factor grade letter <-> numeric (1=A+ best ... 13=F worst); goodness = 14-num
NUM2LET = {1:"A+",2:"A",3:"A-",4:"B+",5:"B",6:"B-",7:"C+",8:"C",9:"C-",10:"D+",11:"D",12:"D-",13:"F"}
LET2NUM = {v:k for k,v in NUM2LET.items()}
FACTORS = ["V","G","P","M","R"]


def label_for(q: float) -> str:
    return ("Strong Buy" if q>=4.5 else "Buy" if q>=3.5 else "Hold" if q>=2.5
            else "Sell" if q>=1.5 else "Strong Sell")


def _from_sa(universe=None) -> pd.DataFrame:
    if not SA_CACHE.exists():
        raise FileNotFoundError(f"ratings cache missing: {SA_CACHE}. Refresh it from the provider snapshot.")
    blob = json.load(open(SA_CACHE))
    rows = []
    for tk, v in blob["ratings"].items():
        f = v.get("factors", {})
        q = v.get("quant")
        rows.append({"ticker": tk, "quant": q, "label": label_for(q) if q is not None else None,
                     **{k: f.get(k, "—") for k in FACTORS}})
    df = pd.DataFrame(rows).dropna(subset=["quant"]).set_index("ticker")
    df["rank_pct"] = df["quant"].rank(pct=True)
    df["sector"] = None  # the ratings cache carries no sector; enrich per-candidate in Tier 2
    df["source"] = "sa"
    df.attrs["asof"] = blob.get("asof_date")
    if universe:
        df = df.loc[df.index.intersection([u.upper() for u in universe])]
    return df.sort_values("quant", ascending=False)


def _from_replica(universe=None) -> pd.DataFrame:
    if CLAWD_SCRIPTS not in sys.path:
        sys.path.insert(0, CLAWD_SCRIPTS)
    from lib.alpha.engine import run_screen          # noqa: E402
    from lib.alpha.grades import compute_grades       # noqa: E402
    screen_df, _corr, _fund = run_screen()
    grades = compute_grades(screen_df)                # {ticker: {grades, quant, score}}
    rows = []
    for tk, row in screen_df.iterrows():
        g = grades.get(tk, {})
        gl = g.get("grades", {})
        rows.append({"ticker": tk, "quant": g.get("score"), "label": g.get("quant"),
                     "V": gl.get("value","—"), "G": gl.get("growth","—"),
                     "P": gl.get("profitability","—"), "M": gl.get("momentum","—"),
                     "R": gl.get("revisions","—"),
                     "rank_pct": row.get("rank_pct"), "sector": row.get("sector")})
    df = pd.DataFrame(rows).set_index("ticker")
    df["source"] = "replica"
    if universe:
        df = df.loc[df.index.intersection([u.upper() for u in universe])]
    return df.sort_values("quant", ascending=False)


def get_universe_scores(source: str = "sa", universe=None) -> pd.DataFrame:
    """Normalized factor-score table. source: 'sa' (local real) | 'replica' (yfinance)."""
    if source == "sa":
        return _from_sa(universe)
    if source == "replica":
        return _from_replica(universe)
    raise ValueError(f"unknown source: {source!r} (use 'sa' or 'replica')")


def _grade_num(x) -> int | None:
    return LET2NUM.get(x) if isinstance(x, str) else None


def gate_strong_buy(df: pd.DataFrame, floor: bool = True) -> pd.DataFrame:
    """AP gate: quant >= 4.5 (Strong Buy) + floor rule (no factor worse than D, i.e. num<=11)."""
    g = df[df["quant"] >= 4.5].copy()
    if floor:
        def passes(r):
            nums = [_grade_num(r[f]) for f in FACTORS]
            nums = [n for n in nums if n is not None]
            return bool(nums) and max(nums) <= 11   # no D- (12) or F (13)
        g = g[g.apply(passes, axis=1)]
    return g.sort_values("quant", ascending=False)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "sa"
    df = get_universe_scores(src)
    sb = gate_strong_buy(df)
    print(f"source={src} asof={df.attrs.get('asof')} | universe={len(df)} | Strong-Buy+floor={len(sb)}")
    print(sb.head(15)[["quant","label","V","G","P","M","R","rank_pct"]].to_string())
