export const meta = {
  name: 'portfolio-run',
  description: 'Equal-weight Strong-Buy book maintenance: given a screened book (KEEP/CUT/BUY from the deterministic gate), write a data-driven weekly-note rationale for each new BUY. Mirrors an actively-rebalanced quant model portfolio — distinct from the 2-pick funnel in alpha_run.js.',
  phases: [{ title: 'Buys', detail: 'weekly-note rationale per new equal-weight add' }],
}

const VENV = '/Users/ethanyang/clawd/.venv/bin/python'
const ENGINE = '/Users/ethanyang/Developer/github.com/YichengYang-Ethan/alpha-quant'
const ANALYZE = `${ENGINE}/scripts/alpha_analyze.py`
const FEWSHOT = (args && args.fewshot) || ''  // local-only exemplar index path, passed at invocation (kept out of source)

// Deterministic screen (run separately) produces the maintenance packet; its essentials are
// passed via args, with the current run's values as fallback (args binding can be flaky).
const FIDELITY = (args && args.fidelity) || 90
const KEPT = (args && args.kept) || 27
const CUT = (args && Array.isArray(args.cut) && args.cut.length) ? args.cut : ['AUGO', 'AU', 'B']
const BUYS = (args && Array.isArray(args.buys) && args.buys.length) ? args.buys
  : ['INTC', 'MXL', 'AMD', 'UCTT', 'AXTI', 'TTMI']
log(`book maintenance: kept ${KEPT}, cut ${CUT.length} (${CUT.join(',')}), writing ${BUYS.length} new buys -> ${BUYS.join(', ')}`)

const RATIONALE = {
  type: 'object', additionalProperties: false,
  required: ['ticker', 'gate_pass', 'conviction', 'rationale', 'key_grades', 'sector'],
  properties: {
    ticker: { type: 'string' },
    gate_pass: { type: 'boolean' },
    conviction: { type: 'number', description: '1-10' },
    sector: { type: 'string' },
    key_grades: { type: 'string', description: 'the 5 real factor grades V/G/P/M/R + quant' },
    rationale: { type: 'string', description: "weekly-note-style buy rationale grounded ONLY in the data package + few-shot" },
  },
}

const buys = await parallel(BUYS.map((tk) => () => agent(
  `You are the analyst for an equal-weight, actively-rebalanced QUANT MODEL PORTFOLIO. ${tk} just entered the ` +
  `Strong-Buy+floor universe and is being ADDED as a new ~3.3% equal-weight position this week. Document the add as a ` +
  `concise weekly-note buy rationale.\n` +
  `STEP 1 — data package: ${VENV} ${ANALYZE} ${tk} --source sa  (real quant + 5 factor grades V/G/P/M/R + factsheet + honesty).\n` +
  (FEWSHOT ? `STEP 2 — similar past adds (style + outcomes): ${VENV} -c "import sys; sys.path.insert(0,'${ENGINE}/scripts/lib'); ` +
  `from thesis_retriever import retrieve, format_fewshot; print(format_fewshot(retrieve('${tk} ' + 'sector theme', k=3, index_path='${FEWSHOT}')))"\n` : '') +
  `STEP 3 — write the rationale in the model-portfolio weekly-note voice: lead with Market Cap + Quant Rating + ` +
  `Sector/Industry rank, then 2-4 sentences on the business and WHY the factor profile (walk the real grades; explain any ` +
  `weak grade — e.g. a soft Value grade is acceptable when Momentum+Revisions lead) supports the add. Note one risk. ` +
  `RULES: use ONLY the package's real grades (never estimate); this is an equal-weight ADD (not a concentrated bet); ` +
  `keep it tight. Set gate_pass from the package and conviction 1-10.`,
  { label: `buy:${tk}`, phase: 'Buys', schema: RATIONALE }
)))

const ok = buys.filter(Boolean)
log(`documented ${ok.length} new buys`)
return {
  mode: 'equal-weight-book-maintenance',
  asof: (args && args.asof) || null,
  benchmark: 'equal-weight S&P (RSP)',
  fidelity_vs_reference_pct: FIDELITY,
  kept: KEPT,
  cut: CUT,
  new_buys: ok.map((b) => ({ ticker: b.ticker, sector: b.sector, conviction: b.conviction,
    key_grades: b.key_grades, rationale: b.rationale })),
  honesty: 'Typical single add ~= coin-flip vs the equal-weight benchmark (median ~-1.5%); the edge is the basket + ' +
    'cutting names that lose Strong-Buy fast while letting winners run. Regime-dependent; gross of weekly-rebalance friction.',
}
