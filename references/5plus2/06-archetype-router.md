# 06 · Company-Archetype Router (makes 5+2 generalize to any ticker) ⭐⭐⭐

> **Why this exists**: the rules in `5plus2-rubric.md` are mostly case-bound (`[NVDA]`,
> `[COST]`, `[bank]`…). Great for familiar names, but a brand-new ticker can only be
> loosely analogized. This table abstracts "cases" into "archetypes": for *any* stock,
> first tag it along 5 axes → look up the playbook for ④ financials / ⑤ valuation / ②
> moat lens / ⑥ bull / ⑦ risks. **The `[TICKER]` tags in the rubric are examples, not
> hard rules.**
> **How to use**: Step 0.5 classify → main routing table → anything that matches nothing
> uses the "universal fallback" at the bottom.

---

## Step 0.5 · Classify on 5 axes (tag the company first)
1. **Profitability state**: ① GAAP-profitable ② non-GAAP profitable but GAAP-loss (high SBC)
   ③ pre-profit / cash-burning → **drives the ⑤ valuation method**
2. **Business model**: semis/hardware · software SaaS · platform/ads · bank/financial ·
   retail/consumer · manufacturing/foundry/heavy-asset · energy/resources · other →
   **drives ④ metrics + ② moat lens**
3. **Capital intensity**: asset-light (cloud/software) · capital-intensive (foundry/AI-infra/
   telecom/IDM) → **drives capex / net-leverage checks**
4. **Growth stage**: high-growth (>30%) · mature compounder · cyclical · turnaround ·
   vision/pre-revenue → **drives ⑥ bull archetype + ⑤ approach**
5. **Leadership & coverage**: founder / professional CEO (**judge both by track record, don't
   mechanically penalize a non-founder**) · is it in the tracking universe? (**decides whether
   to emit a rating card**)

> A company can span types (a platform that is also capital-intensive; a manufacturer that is
> also a story stock) → take the union, lead with the line that drives the stock.

---

## Main routing table (8 archetypes → per-step playbook)

| Archetype | Examples | ② moat lens | ④ financials focus | ⑤ valuation | ⑥ bull | ⑦ top risk cluster |
|---|---|---|---|---|---|---|
| **1 Compute/semi leader (near-monopoly)** | NVDA·TSM | network effect/ecosystem; scale+capital+first-mover; share can drift if the pie grows | **gross margin = supply/demand thermometer**; LT-debt<40%; FCF; heavy-asset → capex covered | forward PE vs SPX/own history; DCF base/bull/bear | shovel-seller / toll-booth certainty | demand miss → margin pressure; competition (in-house chips); supply/geopolitics; **product delay** |
| **2 Quality large-cap platform (profitable)** | MSFT·META·GOOGL·AMZN | network/ecosystem/full-stack; **split growth (AI vs non-AI)** | gross margin (software 80%+); **FCF yield cross-checked vs peers**; segment profit vs revenue | forward PE (tell the re-rating story); a complex conglomerate can be "neither cheap nor expensive"; FCF | certainty + optionality; investor management; **ability to steer results** | regulation/antitrust; cyclical ads; capital overspend; customer concentration |
| **3 High-growth software SaaS** | PLTR·SNOW | **first name "the one thing rivals can't structurally do"** (cross-cloud neutrality); switching costs/data gravity/vertical depth; NRR | growth + *is it accelerating*; NRR>120%; **GAAP-loss → strip SBC → look at FCF margin**; asset-light; net cash incl. converts | profitable→forward PE (high); **GAAP-loss/consumption→EV/Sales + Meritech 20+20 + quality peers**; pre-profit→P/S | AI transition / scarce industry position; high ceiling, firm floor | **paradigm disruption (AI agents bypass the middle layer)**; competition; valuation premium; SBC dilution (if un-bought-back); key-man |
| **4 Story / faith / option stock** | TSLA | value-driver ≠ revenue-driver (value sits in the unproven business) | gross-margin trend; cash flow | **no relative multiples → SOTP-DCF** (discount each line, see where value concentrates) | **conditional bull** ("only if you believe X commercializes") | tech never ships; founder misjudgment/distraction; subsidy roll-off; price already > base |
| **5 Capital-intensive / AI-infra / credit-sensitive** | ORCL | model innovation (capital decoupling) but margin dilutive | **capex/revenue + net leverage (net debt/EBITDA >3 downgrade) + FCF turning negative on capex**; watch rating agencies | forward PE on two legs (EPS × multiple, proxy-stock sentiment); regime-switch re-rating | order backlog visibility; proxy stock | **customer concentration**; **balance-sheet/capex spiral**; AI-demand fragility |
| **6 Bank / financial** | GS | one-stop platform; brand/century-long relationships/capital wall | **efficiency ratio (opex/rev, lower better) + ROTCE + CET1** (gross margin/debt-ratio/FCF do NOT apply) | **P/B × BPS (ROTCE-driven), not PE** | cyclical recovery + structural improvement | **strong-cycle downturn (non-linear)**; systemic (private credit); regulatory capital |
| **7 Retail / consumer-defensive** | COST | membership flywheel/scale-cost/brand; high turns = supplier pricing power | **gross margin can be deliberately low (membership ~11%, "GM=moat" fails) → stable net margin + renewal 90%+ + same-store + turns** | forward PE; **expensive is itself the #1 risk** | defensive counter-cyclical compounder ("sleep well at night") | **valuation rich** (slow to digest + no downside cushion); slow AI/innovation; weakening spending power |
| **8 Turnaround** | INTC | a damaged old moat + a new catalyst | **read the repair slope / inflection, not the absolute level**; heavy-asset → earnings swing hard | **DCF + historical PE both break → "market-cap headroom"** (TAM × share × net margin × PE + option value) | turnaround (new CEO + catalyst + sector beta + expectation gap) | post-rally pullback; yield/execution ramp; can the turnaround become systemic |

① Industry is common to all: classify by source of profit (not surface industry) → TAM (refresh
live from a named firm, narrow definition) → growth/adoption → competitive landscape by
category → industry-level risk. Strong-cyclical = structural discount; consumer = spending power
+ sentiment; hunt the expectation gap.

---

## ⑤ Valuation method (most error-prone → decision tree)
```
Profitability state?
├─ GAAP-profitable
│   ├─ bank/financial ──────────→ P/B × BPS (ROTCE-driven)
│   ├─ normal large-cap/hardware/platform → forward PE (triangulate: SPX ~22-25x / own history / peers)
│   └─ high-growth software (profitable) → forward PE (tolerate higher) + P/S
├─ non-GAAP profitable / GAAP-loss (high SBC, consumption SaaS)
│                          ────→ ⭐ EV/Sales + Meritech rule (growth >20% AND FCF margin >20% earns >10x)
│                                + quality-adjusted peer comp (NOT vs a single rival) + strip SBC, look at FCF
├─ pre-profit
│   ├─ vision/SaaS ─────────────→ forward P/S
│   └─ story/option stock ──────→ SOTP-DCF (discount each line, see where value concentrates)
└─ turnaround / trough earnings → market-cap headroom (TAM × share × net margin × PE + option value)

heavy-asset / capital-intensive overlay → also: capex/revenue + net leverage + is FCF dragged negative by capex
```
**Universal valuation discipline (all archetypes)**: ① give **base / bull / bear** vs price;
② **anchor the DCF base BELOW the analyst mean** (he runs conservative); ③ **target ∈ [base,
bull]** (can sit above base on conviction, ≠ simply the base); ④ range conclusion: under/fair/
over/"neither cheap nor expensive"; ⑤ **valuation ⊥ risk** (⑤ = cheap-or-not, ⑦ = dare-to-buy);
⑥ explain *why* a multiple is structurally high or low.

---

## ④ Financial metrics by archetype (don't apply the wrong set)
- **Universal base (every stock)**: revenue growth + gross margin (level + **trend** + benchmark,
  SPX avg ~32%) + **LT Debt/Total Assets <40%** (Buffett, NOT D/E) + FCF persistently positive +
  net margin.
- **Semis/hardware**: gross margin as a supply/demand thermometer; heavy-asset → capex covered by
  operating CF.
- **Software SaaS**: growth *accelerating?* + NRR>120%; **GAAP-loss → strip SBC first** (add back to
  see real profit) + check buyback offset + **FCF margin >20%**; net cash incl. converts.
- **Capital-intensive/AI-infra**: capex/revenue + net leverage + FCF negative-on-capex + agency actions.
- **Bank**: efficiency ratio + ROTCE + CET1 (gross margin/debt-ratio/FCF do NOT apply).
- **Retail/consumer**: gross margin may be deliberately low → net-margin stability + renewal + same-store + turns.
- **Turnaround/heavy-asset IDM**: read the repair *slope/inflection*, not the absolute level.
- ⚠️ Universal trap: compare margins like-for-like (don't pit gross margin against operating margin);
  over-high margins are themselves fragile (→ ⑦).

---

## ⭐ Universal fallback playbook (anything not matching 1–8: biotech / REIT / insurer / industrial / shipping / utility…)
When no dedicated archetype fits, default to this so the method never breaks:
- **① Industry**: classify by source of profit → web-pull TAM+CAGR (named firm, narrow) →
  enumerate competition → industry-level risk.
- **② Moat**: find "**the one thing rivals structurally cannot do**" (neutrality/license/network/
  scale/switching cost/brand) = the real moat; if money + time can catch up, it's weak.
- **③ Management**: technical/long-tenure/stable culture = positive; **judge by track record**
  (founder or pro CEO alike); concentration = double-edged.
- **④ Financials**: universal base (growth / gross-margin trend / LT-debt<40% / FCF+ / net margin) +
  ROIC; add the industry-specific metric as needed (heavy-asset→capex; lender→loan losses/capital).
- **⑤ Valuation**: profitable→forward PE (vs SPX/own history/peers); unprofitable→EV/Sales or P/S;
  story→SOTP; **always base/bull/bear, base anchored below analyst mean**.
- **⑥ Logic**: one-line bull + precondition; prefer **certainty > upside**; first falsify the popular
  bear narrative with data.
- **⑦ Risk** (always include these 4 + add as needed): ① core driver disappoints (find the single most
  important metric, ask when it breaks) ② competition/share loss ③ **business model bypassed by a new
  paradigm** ④ valuation too high (+ as applicable: leadership concentration / cyclical / regulatory /
  customer concentration / financial fragility). **Don't pile on risks the company has neutralized;
  contextualize, don't catastrophize.**
- **⑦ mantra (always)**: the reason for success, flipped, is the biggest risk.

---

## Self-check (run before output)
- [ ] Classified the archetype? Used the matching ⑤ method (didn't put a bank on PE, a story stock
      on relative multiples, or judge a consumption-SaaS vs a single rival)?
- [ ] Is the TAM a live, named-firm, narrow-definition figure (not a stale/hand-wavy number)?
- [ ] DCF base anchored below the analyst mean? Target ∈ [base, bull]?
- [ ] Does ⑦ include the paradigm-disruption layer? No piled-on, already-neutralized risks?
- [ ] Is the name in the tracking universe? If not → no rating card, just understanding + valuation range.
- [ ] Matched none of 1–8? Used the universal fallback instead of force-fitting the closest case?
