# alpha-quant — a factor-screen + LLM deep-analysis engine

A quantitative stock screener fused with an LLM analysis layer. A cross-sectional
**momentum + earnings-revisions** factor rating is the gate; an LLM **thesis
writer** produces cards in a disciplined Quant voice; a **mechanical
entry/exit discipline** governs the book — all wrapped in an honest, regime-aware
funnel.

One shared engine drives **two pick modes** (mirroring two real quant products):

| Mode | Folder | What it does |
|---|---|---|
| **picks** | `workflows/picks/` | concentrated funnel — screen → Strong-Buy gate → analyze a shortlist → **adversarially verify** → rank to a top-N (2-pick cadence). `alpha_run.js` (debate) + `alpha_run_pure.js` (pass-through). |
| **portfolio** | `workflows/portfolio/` | equal-weight, actively-rebalanced **book maintenance** — screen the held book → KEEP / CUT / BUY → write a weekly-note rationale per add, benchmarked to an equal-weight index. `portfolio_run.js`. |

Plus a **deep-analysis skill** — `/alpha-quant TICKER` — a data-grounded thesis
card for one name (installed locally, not shipped here).

> ⚠️ **Method, not data.** This repo ships the *engine and methodology* only.
> The rating data, thesis corpora, and pick ledgers come from a **premium
> quant-ratings provider** and **stay local** (git-ignored), per that provider's
> terms. Plug in your own factor source to run it.

## Layout

```
shared/                      the engine — used by BOTH modes
  lib/universe_scores.py       data-source abstraction + Strong-Buy/floor gate
  lib/thesis_retriever.py      few-shot retrieval over a thesis corpus (index_path-pluggable)
  alpha_analyze.py             Tier-2 atom: full data package for one name
  build_fewshot_index.py       build a local few-shot index
workflows/
  picks/                       concentrated pick funnel (alpha_run, alpha_run_pure)
  portfolio/                   equal-weight book maintenance (portfolio_run)
data/                          LOCAL ONLY (git-ignored) — provider data per namespace
```

## The funnel

```
TIER 0-1  breadth · deterministic · ~0 LLM
  universe → factor scores → Strong-Buy gate (+ floor rule) → de-dupe → shortlist/book
                ▲ data-source abstraction: "sa" (provider ratings, local) | "replica" (computed, portable)
TIER 2    depth · LLM · shortlist/buys only
  per candidate: real grades + factsheet + few-shot exemplars (+ outcomes) → thesis/rationale
TIER 3    judgment · LLM + code
  picks: adversarial bear-case refutation → rank survivors → top-N + exit plan
  portfolio: KEEP/CUT/BUY deltas vs the held book → weekly-note rationale per add
```

**Why this shape:** the rating/ranking is *deterministic code* (never
LLM-estimated), so the LLM spends tokens only on the shortlist/buys and only on
judgment/narrative — cost scales with the shortlist, not the ~4,000-name universe.

## Data-source abstraction

`shared/lib/universe_scores.py :: get_universe_scores(source)` returns one
normalized table regardless of origin; both modes consume it identically:

| source | what | fidelity |
|---|---|---|
| `replica` | computed factor proxies (value/growth/profitability/momentum/revisions, percentile-ranked) | approximate, portable |
| `sa` | a premium provider's real Quant ratings cache (full market) | exact, local only |

## Usage

```bash
# screen the universe + Strong-Buy gate
python shared/lib/universe_scores.py replica          # computed proxies
python shared/lib/universe_scores.py sa               # local provider ratings

# one-name deep-analysis data package (feeds /alpha-quant or either workflow)
python shared/alpha_analyze.py NVDA --source sa

# picks funnel:        run workflows/picks/alpha_run.js      via the Workflow tool
# portfolio maintenance: run workflows/portfolio/portfolio_run.js via the Workflow tool
```

## The honesty layer (the point)

The reverse-engineered rating is ~65% momentum + EPS-revisions. A multi-year
event study shows a **typical single top-rated pick is roughly a coin-flip vs the
benchmark** (negative-to-flat median) and is **regime-dependent** (weak in choppy
momentum years, strong in trending ones). The edge is **cutting losers fast while
a few winners compound**, not per-pick hit-rate. So this is a **filter +
framework + discipline**, *not* a "this will go up" signal. Every output carries
that caveat; the picks mode adversarially tries to *refute* each thesis, and the
portfolio mode reports the honest cut/held asymmetry.

## Related

This is the open engine. The rating recipe, provider-specific ingestion/analysis
tooling, and the data manifest live in a **private companion repo**
(access-controlled):
[`alpha-quant-core`](https://github.com/YichengYang-Ethan/alpha-quant-core). The
paid datasets stay local and are referenced there, never uploaded.

## License / compliance

Personal research. The methodology is an independent distillation. Paid
third-party data is never included or republished; see `.gitignore`.
