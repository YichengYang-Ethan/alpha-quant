# alpha-quant — a factor-screen + LLM deep-analysis engine

A quantitative stock screener fused with an LLM deep-analysis layer. A
cross-sectional **momentum + earnings-revisions** factor rating is the gate, an
LLM **thesis writer** produces a single-name card in a disciplined Quant voice,
and a **mechanical entry/exit discipline** governs the book — all wrapped in an
honest, regime-aware funnel.

Two outputs, one shared substrate:

- **Deep analysis** — `/alpha-quant TICKER` (a Claude skill): a data-grounded
  thesis card for one name, with real factor grades, fundamentals, retrieved
  exemplars, and a calibrated honesty layer.
- **Picking** — `alpha-run` (a workflow): screen the universe → gate to Strong
  Buy → de-dupe → analyze a shortlist in parallel → **adversarially verify** →
  rank to a top-N.

> ⚠️ **Method, not data.** This repo ships the *engine and methodology* only.
> The rating data, the thesis corpus, and the pick ledger come from a **premium
> quant-ratings provider** and **stay local** (git-ignored), per that provider's
> terms. Plug in your own factor source to run it.

## The funnel

```
TIER 0-1  breadth · deterministic · ~0 LLM
  universe → factor scores → Strong-Buy gate (+ floor rule) → de-dupe → shortlist
                ▲ data-source abstraction: "sa" (provider ratings, local) | "replica" (computed, portable)
TIER 2    depth · LLM · shortlist only
  per candidate: real grades + factsheet + few-shot exemplars (+ outcomes) → thesis card
TIER 3    judgment · LLM + code
  adversarial bear-case refutation → rank survivors → top-N picks + mechanical exit plan
```

**Why this shape:** the rating/ranking is *deterministic code* (never
LLM-estimated), so the LLM spends tokens only on the shortlist and only on
judgment/narrative — cost scales with the shortlist, not the ~4,000-name universe.

## Data-source abstraction

`scripts/lib/universe_scores.py :: get_universe_scores(source)` returns one
normalized table regardless of origin:

| source | what | fidelity |
|---|---|---|
| `replica` | computed factor proxies (value/growth/profitability/momentum/revisions, percentile-ranked) | approximate |
| `sa` | a premium provider's real Quant ratings cache (full market) | exact (local only) |

The skill and workflow consume this table identically, so the factor source is
pluggable.

## Components (public)

| File | Role |
|---|---|
| `scripts/lib/universe_scores.py` | data-source abstraction + Strong-Buy/floor gate |
| `scripts/lib/thesis_retriever.py` | few-shot retrieval over the thesis corpus (theme + keyword) |
| `scripts/build_fewshot_index.py` | build the local few-shot index |
| `scripts/alpha_analyze.py` | **Tier-2 atom**: assemble the full data package for one name |
| `workflows/alpha_run.js` | **the picking funnel** (Tier 2-3 orchestration) |
| `/alpha-quant` | the deep-analysis Claude skill (installed locally; not shipped in this repo) |

*(Provider-specific tooling — corpus build, rating reverse-engineering, replicas
— is kept local; see `.gitignore`.)*

## Usage

```bash
# screen the universe + Strong-Buy gate
python scripts/lib/universe_scores.py replica          # computed proxies
python scripts/lib/universe_scores.py sa               # local provider ratings

# one-name deep-analysis data package (feeds /alpha-quant or the workflow)
python scripts/alpha_analyze.py NVDA --source sa

# picking funnel (multi-agent): run workflows/alpha_run.js via the Claude Code Workflow tool
```

## The honesty layer (the point)

The reverse-engineered rating is ~65% momentum + EPS-revisions. A 7-year event
study shows a **typical single top-rated pick underperforms the market at 3
months (median ≈ −2.5%)** and is **regime-dependent** (weak in choppy momentum
years, strong in trending ones). So this is a **filter + framework + discipline**,
*not* a "this will go up" signal. Every output carries that caveat, and the
Tier-3 verifier adversarially tries to *refute* each thesis — in a momentum-top
regime it will (correctly) reject an entire shortlist rather than manufacture
conviction.

## Related

This is the open engine. The rating recipe, the provider-specific tooling, and
the data manifest live in a **private companion repo** (access-controlled):
[`alpha-quant-core`](https://github.com/YichengYang-Ethan/alpha-quant-core). The
paid datasets stay local and are referenced there, never uploaded.

## License / compliance

Personal research. The methodology is an independent distillation. Paid
third-party data is never included or republished; see `.gitignore`.
