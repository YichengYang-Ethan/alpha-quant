#!/usr/bin/env python3
"""Defined-risk options-income idea generator (premium-selling overlay).

Given a ticker, propose a short-premium income idea — a cash-secured put or a
bull put spread — targeting a configurable probability-of-profit (POP) and
days-to-expiry (DTE). POP is computed Black-Scholes (N(d2)) from the option
chain's implied volatility; no scipy. This is a generic income/overlay tool that
pairs with a fundamental screen: only sell puts on names you would be happy to
own, size small, keep cash for assignment, and manage by closing near ~50% of
max profit.

Usage: python shared/options_income.py NVDA [--dte 45] [--pop 0.75] [--width 5]
Data: yfinance option chains. Not investment advice.
"""
import argparse, math
from datetime import datetime, timezone

R_FREE = 0.044  # ~ risk-free rate


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def pop_short_put(S, K, iv, T):
    """Approx probability a short put expires OTM (price stays >= K) = N(d2)."""
    if iv <= 0 or T <= 0 or S <= 0 or K <= 0:
        return None
    d2 = (math.log(S / K) + (R_FREE - 0.5 * iv * iv) * T) / (iv * math.sqrt(T))
    return ncdf(d2)


def mid(row):
    b, a, last = row.get("bid", 0) or 0, row.get("ask", 0) or 0, row.get("lastPrice", 0) or 0
    return (b + a) / 2 if (b > 0 and a > 0) else (last or b or a)


def main():
    import yfinance as yf
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("--dte", type=int, default=45, help="target days to expiry")
    ap.add_argument("--pop", type=float, default=0.75, help="target probability of profit (0-1)")
    ap.add_argument("--width", type=float, default=0.0, help="spread width in dollars (0=auto, ~3pct of price)")
    a = ap.parse_args()

    tk = yf.Ticker(a.ticker)
    try:
        S = float(tk.fast_info["lastPrice"])
    except Exception:
        S = float(tk.history(period="1d")["Close"].iloc[-1])
    exps = tk.options
    if not exps:
        print(f"no options chain for {a.ticker}"); return
    today = datetime.now(timezone.utc).date()
    dte_of = lambda e: (datetime.strptime(e, "%Y-%m-%d").date() - today).days
    exp = min(exps, key=lambda e: abs(dte_of(e) - a.dte))
    dte = dte_of(exp); T = dte / 365
    puts = tk.option_chain(exp).puts
    puts = puts[(puts["strike"] < S) & (puts["bid"] > 0)].copy()
    if puts.empty:
        print(f"no OTM puts with quotes for {a.ticker} {exp}"); return

    width = a.width or round(max(S * 0.03, 1), 0)
    best = None
    for _, row in puts.iterrows():
        K = float(row["strike"]); iv = float(row.get("impliedVolatility") or 0)
        p = pop_short_put(S, K, iv, T)
        if p is None:
            continue
        score = abs(p - a.pop)
        if best is None or score < best["score"]:
            best = {"score": score, "K": K, "iv": iv, "pop": p, "mid": mid(row)}
    if not best:
        print("could not price a short put"); return
    Ks, iv, pop, short_mid = best["K"], best["iv"], best["pop"], best["mid"]

    longs = puts[puts["strike"] <= Ks - width]
    long_row = longs.iloc[(longs["strike"] - (Ks - width)).abs().argmin()] if not longs.empty else None
    spread = None
    if long_row is not None:
        Kl = float(long_row["strike"]); credit = round(short_mid - mid(long_row), 2)
        w = round(Ks - Kl, 2); max_risk = round(w - credit, 2)
        spread = {"short": Ks, "long": Kl, "width": w, "credit": credit,
                  "max_reward": round(credit * 100, 0), "max_risk": round(max_risk * 100, 0),
                  "breakeven": round(Ks - credit, 2),
                  "ror": round(credit / max_risk, 3) if max_risk > 0 else None,
                  "credit_to_width": round(credit / w, 3) if w else None}

    print(f"\n=== options-income idea: {a.ticker} @ ${S:.2f} | exp {exp} ({dte} DTE) ===")
    print(f"short put {Ks} | IV {iv:.0%} | POP(expire OTM) ~{pop:.0%} (target {a.pop:.0%})")
    if spread:
        print(f"\n[DEFINED-RISK] bull put spread: sell {spread['short']}P / buy {spread['long']}P (width ${spread['width']})")
        print(f"  credit ~${spread['credit']:.2f} (credit/width {spread['credit_to_width']:.0%}; aim >=33%)")
        print(f"  max reward ${spread['max_reward']:.0f} / max risk ${spread['max_risk']:.0f} (ROR {spread['ror']:.0%}) | breakeven {spread['breakeven']}")
    print(f"\n[CASH-SECURED PUT] sell {Ks}P credit ~${short_mid:.2f} "
          f"(secure ${Ks*100:.0f}, BE {round(Ks-short_mid,2)}, ~{(short_mid/Ks)*(365/dte):.0%} annualized if OTM)")
    print("\nManage: close near ~50% of max profit; roll the short leg if tested. "
          "Only sell puts on names you'd own; size small; keep cash for assignment. Not advice.")


if __name__ == "__main__":
    main()
