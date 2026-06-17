#!/usr/bin/env python3
"""Trend-following ETF rotation (risk-on/off overlay).

A classic, fully-mechanical overlay: each month-end, hold equal-weight the menu
ETFs trading above their long-term moving average (default 200-day), and park the
rest in T-bills (BIL) when their trend is broken. Backtests vs SPY / QQQ buy-and-
hold and prints the CURRENT positioning. Trend-following trades some upside for
smaller drawdowns; read the max-DD column, not just CAGR.

Usage: python shared/etf_rotation.py [--start 2018-01-01] [--ma 200]
Data: yfinance. Not investment advice.
"""
import argparse
import pandas as pd

MENU = ["SPY", "QQQ", "IWM", "IEMG", "EFA", "GLD"]   # risk-on universe
CASH = "BIL"                                          # risk-off (T-bills)


def load(tickers, start):
    import yfinance as yf
    data = yf.download(sorted(set(tickers)), start=start, auto_adjust=True, progress=False)
    close = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data.to_frame()
    return close.dropna(how="all")


def stats(equity):
    r = equity.pct_change().dropna()
    yrs = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / yrs) - 1
    vol = r.std() * (252 ** 0.5)
    sharpe = (r.mean() * 252) / vol if vol else 0
    dd = (equity / equity.cummax() - 1).min()
    return cagr, vol, sharpe, dd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2018-01-01")
    ap.add_argument("--ma", type=int, default=200, help="trend moving-average window (days)")
    a = ap.parse_args()

    px = load(MENU + [CASH, "SPY", "QQQ"], a.start)
    sma = px.rolling(a.ma).mean()
    me = px.resample("ME").last().index
    daily = px.pct_change().fillna(0)

    eq, curve, log = 1.0, [], []
    for i in range(len(me) - 1):
        t0, t1 = me[i], me[i + 1]
        on = [e for e in MENU if e in px.columns and px[e].asof(t0) > (sma[e].asof(t0) or 1e18)]
        holds = on if on else [CASH]
        w = pd.Series({h: 1 / len(holds) for h in holds})
        seg = (daily.loc[(daily.index > t0) & (daily.index <= t1), list(w.index)] * w).sum(axis=1)
        for d, ret in seg.items():
            eq *= (1 + ret); curve.append((d, eq))
        log.append((str(t0.date()), on))
    rot = pd.Series(dict(curve)).sort_index()

    print(f"=== Trend-following ETF rotation ({a.ma}d trend, monthly, equal-wt risk-on else {CASH}) ===")
    print(f"menu {MENU} | as of {px.index.max().date()}\n")
    print(f"{'strategy':16}{'CAGR':>8}{'vol':>8}{'Sharpe':>8}{'maxDD':>8}")
    for name, eqs in [("rotation", rot),
                      ("buy&hold SPY", (px['SPY'].dropna() / px['SPY'].dropna().iloc[0])),
                      ("buy&hold QQQ", (px['QQQ'].dropna() / px['QQQ'].dropna().iloc[0]))]:
        c, v, s, dd = stats(eqs)
        print(f"{name:16}{100*c:>7.1f}%{100*v:>7.1f}%{s:>8.2f}{100*dd:>7.1f}%")

    tnow = px.index.max()
    on_now = [e for e in MENU if e in px.columns and px[e].asof(tnow) > sma[e].asof(tnow)]
    print(f"\nCURRENT positioning ({tnow.date()}): risk-on = {', '.join(on_now) or 'NONE -> cash (' + CASH + ')'}")
    for e in MENU:
        if e in px.columns:
            p, m = float(px[e].asof(tnow)), float(sma[e].asof(tnow))
            print(f"  {e:5} {p:>9.2f}  {a.ma}d {m:>9.2f}  {'uptrend' if p > m else 'below trend'}")
    print("\nTrend-following: smaller drawdowns, usually lags buy-and-hold in trending bull markets. Not advice.")


if __name__ == "__main__":
    main()
