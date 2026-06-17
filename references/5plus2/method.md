# 01 · The 5+2 Method (overview)

> **Origin.** The "5+2 method" is a fundamental-analysis framework popularized by **Meitou
> (MeiTouJun)**, a Chinese-language YouTube channel covering US equities. This skill is an
> independent distillation of that *framework* (the steps, thresholds, and judgement style) —
> it does not reproduce the channel's videos or transcripts.

## Definition (as the author frames it)
> The 5+2 method understands a company from **7 angles**. The first five are objective; the
> last two are subjective.
>
> - **The 5 (objective):** ① industry · ② business model · ③ management · ④ financials · ⑤ valuation
> - **The 2 (subjective):** ⑥ investment logic (my reasons *to* buy) · ⑦ investment risk (forcing
>   myself to find reasons *not* to buy)
>
> After the full pass you have a **preliminary but complete** understanding of the company. It is
> the *start* of understanding, not a buy/sell signal.

## What the output is for
A research brief that delivers three things:
1. **Full understanding** — what the company actually is and how it makes money.
2. **Is it fairly valued** — cheap / fair / expensive / "neither cheap nor expensive", with a
   base/bull/bear range.
3. **Bull case vs bear case** — the investment logic weighed against the risks.

## Signature judgement habits
- Pin the **single most important industry trend** first (what *really* drives the stock).
- **Certainty > upside** — prefer the most durable model with the most assured demand.
- **Gross margin is often the most important number** (and its *trend*: rising = demand > supply).
- **LT Debt / Total Assets < 40%** is the balance-sheet safety line (a Buffett heuristic).
- **The reason for success, flipped, is the biggest risk.**
- **End humbly** — "just a starting point, for reference."

## How this skill is built
- `scripts/factsheet.py` — **fact layer**: pulls hard numbers from `yfinance` only, makes no
  judgement.
- `SKILL.md` — **judgement layer**: the 7-step framework + archetype routing + the author's voice.
- `references/06-archetype-router.md` — classify *any* company first, then apply the matching
  playbook (this is what makes the method generalize beyond the names it was distilled from).

> Not investment advice. This reproduces an analytical *framework*; it does not guarantee returns.
