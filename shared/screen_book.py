#!/usr/bin/env python3
"""Deterministic equal-weight Strong-Buy book screen (generic).

Prints the top-N Strong-Buy + floor names as an equal-weight book (JSON). This is
the first, deterministic step of workflows/portfolio/portfolio_run.js — run by its
screen agent so the workflow is self-wired (no external args, no file reads in JS).

  python shared/screen_book.py --n 12 --source sa
"""
import sys, json, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.universe_scores import get_universe_scores, gate_strong_buy  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--source", default="sa", choices=["sa", "replica"])
    a = ap.parse_args()
    uni = get_universe_scores(a.source)
    sb = gate_strong_buy(uni)
    book = [{"ticker": t, "quant": round(float(uni.loc[t, "quant"]), 2)} for t in sb.index[: a.n]]
    print(json.dumps({"source": a.source, "asof": uni.attrs.get("asof"),
                      "n": len(book), "weight_each": round(1 / len(book), 4) if book else 0,
                      "book": book}))


if __name__ == "__main__":
    main()
