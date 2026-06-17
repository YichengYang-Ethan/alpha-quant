# Architecture

## Design premise

A disciplined quant pick service is two things fused: a **breadth** problem (scan
a universe, rank by a factor gate) and a **depth** problem (write a defensible
thesis for a chosen name). Breadth wants deterministic code + parallelism; depth
wants an LLM with the right context. So the system is **layered**, not monolithic:

- **Skill** (`/alpha-quant`) = the depth *atom* — one name, deep, usable standalone.
- **Workflow** (`alpha-run`) = the breadth *assembly line* — it calls the atom's
  logic across a shortlist and adds selection.

They share one substrate: the deterministic factor engine, the data adapters,
the few-shot corpus index, and the calibrated honesty layer.

## The three tiers

### Tier 0-1 — screen & gate (deterministic, ~0 LLM)
`get_universe_scores(source)` → normalized `{quant, V/G/P/M/R, rank_pct, sector}`.
`gate_strong_buy()` keeps `quant ≥ 4.5` **and** the floor rule (no factor worse
than D). Then de-dupe versus the existing book. Output: a shortlist of ~8-40.
This is pure code — the universe can be ~4,000 names at zero LLM cost.

### Tier 2 — analyze (LLM, shortlist only)
`alpha_analyze.py` assembles a **data package** per candidate: real factor grades
(the gate) + a fundamentals/valuation/technicals factsheet + **K few-shot
exemplars** retrieved from the past-thesis corpus (with their *realized
outcomes*) + ledger context + the honesty caveat. The LLM writes the thesis card
from that package — **it never recomputes the factor math**.

### Tier 3 — verify & select (LLM + code)
Each thesis faces an **independent adversarial verifier** prompted to *refute* it
(valuation trap, momentum exhaustion, an explained-away weak factor, regime
risk). Survivors are ranked by conviction → top-N, each with a mechanical exit
plan (180-day-Hold sell / downgrade sell / winners-circle trim).

## Key optimizations

1. **Gate-first funnel** — LLM touches only the shortlist; cost ∝ shortlist, not universe.
2. **Code does math, LLM does judgment** — factor scores are deterministic and reproducible; the LLM handles narrative, risk, and the go/no-go call.
3. **Data-source abstraction** — provider ratings (local, exact) vs computed proxies (portable) behind one interface; downstream is source-agnostic.
4. **Retrieval-augmented few-shot** — retrieve the K most-similar past theses (by theme + keyword) instead of stuffing the whole corpus; keeps context small and the paid corpus local.
5. **Outcome-grounded honesty** — every output carries the event-study calibration (single-name ≈ coin-flip; basket + discipline; regime-dependent).
6. **Adversarial verification** — a skeptic per thesis; it rejects rather than rubber-stamps. A momentum-top, theme-clustered shortlist can legitimately yield *zero* survivors.
7. **Deterministic orchestration** — the workflow makes the funnel reproducible (same universe + date → same shortlist); the LLM is confined to Tiers 2-3.

## Public / private split

- **Public (this repo):** the generic engine code, the workflow, and these docs.
- **Local-only (git-ignored):** the provider's ratings cache, the thesis corpus,
  the pick ledger, the few-shot index built from them, the decoded rating recipe
  (the "secret sauce"), and the provider-specific tooling.

This mirrors how a quant shop open-sources a framework while keeping its data and
its edge proprietary.

## Known refinement

The top-N by raw `quant` is **theme-clustered** (e.g., a top tilted toward one
hot sector), so the adversarial bear case rhymes across the whole shortlist. A
production screen should **de-cluster** — take the top Strong Buy *per
theme/sector* — so survivors get a fair hearing and the output is diversified.
