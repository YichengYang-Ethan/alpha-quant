export const meta = {
  name: 'alpha-run-pure',
  description: 'Pass-through Quant logic: the Strong-Buy gate selects; write a bull thesis + mechanical exit for each pick. NO adversarial verification, NO de-clustering, NO veto — the data-driven rating IS the decision, and risk is managed by the mechanical exit. (Mirrors how a flagship Quant pick service actually picks.)',
  phases: [{ title: 'Pick', detail: 'bull thesis + mechanical exit per selected Strong Buy' }],
}

// Pass-through = the Quant gate IS the selection. These are this period's picks: the top
// fresh Strong Buys (gate + floor, not already in the book), by Quant rank. A typical
// service adds ~2/month. Computed inline by the deterministic screen; override via args.picks.
const VENV = '/Users/ethanyang/clawd/.venv/bin/python'
const ANALYZE = '/Users/ethanyang/Developer/github.com/YichengYang-Ethan/alpha-quant/shared/alpha_analyze.py'
const DEFAULT_PICKS = ['INTC', 'AMD']
const picksIn = (args && Array.isArray(args.picks) && args.picks.length) ? args.picks : DEFAULT_PICKS
log(`pass-through picks: writing theses for ${picksIn.length} Quant-selected names -> ${picksIn.join(', ')}`)

const THESIS = {
  type: 'object', additionalProperties: false,
  required: ['ticker', 'gate_pass', 'conviction', 'thesis_card', 'key_catalyst', 'key_risk', 'exit_plan'],
  properties: {
    ticker: { type: 'string' },
    gate_pass: { type: 'boolean', description: 'did it clear the Strong-Buy + floor gate (it should — that is why it was picked)' },
    conviction: { type: 'number', description: '1-10' },
    thesis_card: { type: 'string', description: "Quant-voice BULL thesis card grounded ONLY in the data package" },
    key_catalyst: { type: 'string' },
    key_risk: { type: 'string', description: 'a noted risk (step 7 disclosure) — NOT a reason to reject' },
    exit_plan: { type: 'string', description: 'mechanical exit triggers' },
  },
}

const picks = await parallel(picksIn.map((tk) => () => agent(
  `You are the Quant pick analyst. ${tk} has ALREADY been SELECTED — it cleared the Quant Strong-Buy gate, and in this ` +
  `pass-through process the data-driven rating IS the decision (no second-guessing, no bear-case veto). Your job is to ` +
  `JUSTIFY and document the pick.\n` +
  `STEP 1 — run: ${VENV} ${ANALYZE} ${tk} --source sa  (returns real grades + factsheet + few-shot + honesty).\n` +
  `STEP 2 — write the BULL thesis card in a disciplined, data-driven Quant voice, 7 steps: (1) Quant gate: walk the 5 grades, ` +
  `explain-away any weak grade (e.g. a weak Value grade is fine — momentum+revisions override it). (2) earnings momentum ` +
  `(rev growth/beat/margins). (3) EPS revisions direction. (4) relative valuation (PEG/fwdPE — note it, do not reject on it). ` +
  `(5) structural theme. (6) catalyst (guidance raise / M&A). (7) a NOTED risk (one paragraph disclosure) + the MECHANICAL ` +
  `exit: 180-day Hold -> sell; downgrade to Sell -> sell; double -> Winner's Circle trim.\n` +
  `RULES: this is a PICK being added to the portfolio — present it as such. Use ONLY the package's real factor scores ` +
  `(never estimate). Do NOT reject it and do NOT write an adversarial bear case — this mode trusts the Quant and relies ` +
  `on the mechanical exit to cut it later if the rating degrades. Keep the honesty caveat (basket-level) at the end.`,
  { label: `pick:${tk}`, phase: 'Pick', schema: THESIS }
)))

const ok = picks.filter(Boolean)
log(`pass-through: ${ok.length} picks documented -> ${ok.map((p) => p.ticker).join(', ')}`)
return {
  mode: 'pass-through',
  asof: (args && args.asof) || null,
  n: ok.length,
  note: 'Quant gate selected these; no verification/veto. Manage by the mechanical exit rules.',
  picks: ok.map((p) => ({
    ticker: p.ticker, conviction: p.conviction, key_catalyst: p.key_catalyst,
    key_risk: p.key_risk, exit_plan: p.exit_plan, thesis_card: p.thesis_card,
  })),
}
