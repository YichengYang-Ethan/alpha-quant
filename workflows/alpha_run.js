export const meta = {
  name: 'alpha-run',
  description: 'Quant funnel: analyze a Strong-Buy shortlist in a data-driven Quant voice -> adversarially verify -> rank to top picks',
  phases: [
    { title: 'Analyze', detail: 'per-candidate Quant thesis from the real data package' },
    { title: 'Verify', detail: 'adversarial bear-case refutation, then rank' },
  ],
}

// Tier 0-1 (deterministic screen -> shortlist) is done INLINE before this runs and
// passed via args.shortlist. This workflow spends LLM only on the shortlist (Tier 2-3).
const VENV = '/Users/ethanyang/clawd/.venv/bin/python'
const ANALYZE = '/Users/ethanyang/Developer/github.com/YichengYang-Ethan/alpha-quant/scripts/alpha_analyze.py'

// args.shortlist (computed inline by the deterministic screen) overrides this demo default.
// Demo default: a de-clustered shortlist (top Strong-Buys, <=2 per sector) so the
// adversarial verifier sees diverse setups instead of one crowded theme.
const DEFAULT_SHORTLIST = ['INTC', 'AMD', 'NBIS', 'ATEX', 'RFIL', 'CVGI', 'QTTB', 'NDLS', 'CNC', 'ALTO', 'SEZL', 'XOM']
let shortlist = (args && Array.isArray(args.shortlist) && args.shortlist.length) ? args.shortlist : DEFAULT_SHORTLIST
if (typeof args === 'string') { try { const p = JSON.parse(args); if (p.shortlist) shortlist = p.shortlist } catch (e) {} }
if (!shortlist.length) { log('no shortlist'); return { error: 'no shortlist' } }
log(`alpha-run: ${shortlist.length} candidates -> ${shortlist.join(', ')}`)

const THESIS = {
  type: 'object', additionalProperties: false,
  required: ['ticker', 'gate_pass', 'conviction', 'thesis_card', 'key_catalyst', 'key_risk', 'exit_plan'],
  properties: {
    ticker: { type: 'string' },
    gate_pass: { type: 'boolean', description: 'did it pass Strong-Buy + floor gate per the data package' },
    conviction: { type: 'number', description: '1-10 strength of the AP-style case' },
    thesis_card: { type: 'string', description: "Quant-style thesis card grounded ONLY in the data package" },
    key_catalyst: { type: 'string' },
    key_risk: { type: 'string' },
    exit_plan: { type: 'string', description: 'mechanical exit triggers' },
  },
}
const REFUTE = {
  type: 'object', additionalProperties: false,
  required: ['lens', 'refuted', 'reason'],
  properties: {
    lens: { type: 'string' },
    refuted: { type: 'boolean', description: 'true ONLY if this lens reveals a FATAL, thesis-invalidating flaw (not a mere risk)' },
    reason: { type: 'string' },
  },
}

const results = await pipeline(
  shortlist,
  (tk) => agent(
    `You are the Quant factor analyst. STEP 1 — run this to get the deterministic data package for ${tk}:\n` +
    `  ${VENV} ${ANALYZE} ${tk} --source sa\n` +
    `It returns: gate (real provider quant + 5 factor grades V/G/P/M/R + strong_buy_and_floor), factsheet ` +
    `(valuation/quality/growth/technicals/news), few-shot (similar past picks' theses + their realized outcomes), ` +
    `ledger_context (is it an AP pick), honesty (basket-level caveat).\n\n` +
    `STEP 2 — write a thesis card in a disciplined, data-driven Quant voice following the 7-step framework: ` +
    `(1) Quant gate: is it Strong Buy? walk the 5 grades; flag/explain any weak grade. ` +
    `(2) earnings momentum: revenue growth (accelerating?), beat, margin trend. ` +
    `(3) EPS revisions: direction (up=fuel, down=exit-precursor). ` +
    `(4) relative valuation: PEG/fwdPE vs peers — note cheap/expensive, but momentum+revisions can override. ` +
    `(5) structural theme. (6) catalyst: prefer guidance raises / M&A (NOT S&P-500 inclusion — not an AP pattern). ` +
    `(7) risk + MECHANICAL exit: 180-day Hold -> sell; downgrade to Sell -> sell; double -> Winner's Circle trim.\n` +
    `RULES: factor scores come ONLY from the package — NEVER estimate them. Use the few-shot exemplars for voice/structure ` +
    `and to sanity-check whether similar setups worked. Set conviction 1-10. Keep the card tight. ` +
    `If the package shows gate FAIL, say so and set gate_pass=false.`,
    { label: `analyze:${tk}`, phase: 'Analyze', schema: THESIS }
  ),
  // Panel verify: 3 diverse-lens skeptics; a name SURVIVES unless >=2 lenses find a
  // FATAL (thesis-invalidating) flaw. One aggressive skeptic no longer kills a good name.
  (thesis, tk) => {
    const LENSES = [
      ['valuation', 'a valuation trap — rich multiple / weak Value grade / multiple-compression risk on a name that already ran'],
      ['momentum_regime', 'momentum exhaustion or adverse regime — the rating is ~65% momentum+revisions and reverses when the trend breaks (check the live tape)'],
      ['fundamentals', 'business/execution fragility — one-off or deteriorating financials, customer concentration, or a cyclical trough mislabeled as growth'],
    ]
    return parallel(LENSES.map(([k, q]) => () => agent(
      `You are a skeptic refuting the bull thesis for ${tk} STRICTLY VIA THE "${k}" LENS (${q}). ` +
      `Thesis: ${JSON.stringify(thesis).slice(0, 1800)}\n` +
      `Set refuted=true ONLY if this lens reveals a FATAL, thesis-invalidating flaw — NOT a mere risk a disciplined ` +
      `holder would accept given the mechanical exit (downgrade->sell, 180-day-Hold->sell). Be specific and grounded.`,
      { label: `verify:${tk}:${k}`, phase: 'Verify', schema: REFUTE })))
      .then((votes) => {
        const v = votes.filter(Boolean)
        const refuted = v.filter((x) => x.refuted).length
        return { ...thesis, verdict: { survives: refuted < 2, refuted_count: refuted, n_lenses: v.length, votes: v } }
      })
  }
)

const ok = results.filter(Boolean)
const survivors = ok.filter((r) => r.gate_pass && r.verdict && r.verdict.survives)
survivors.sort((a, b) => (b.conviction || 0) - (a.conviction || 0))
const picks = survivors.slice(0, 2)
log(`analyzed ${ok.length} | survived verify ${survivors.length} | top picks: ${picks.map((p) => p.ticker).join(', ') || '(none)'}`)

return {
  asof: (args && args.asof) || null,
  analyzed: ok.length,
  survived: survivors.length,
  top_picks: picks.map((p) => ({
    ticker: p.ticker, conviction: p.conviction, key_catalyst: p.key_catalyst,
    key_risk: p.key_risk, exit_plan: p.exit_plan, thesis_card: p.thesis_card,
  })),
  ranked: ok.map((r) => ({
    ticker: r.ticker, conviction: r.conviction, gate_pass: r.gate_pass,
    survives: r.verdict && r.verdict.survives,
    refuted_count: r.verdict && r.verdict.refuted_count,
    bear: ((r.verdict && r.verdict.votes) || []).filter((v) => v.refuted).map((v) => `${v.lens}: ${v.reason}`),
  })),
}
