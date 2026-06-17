export const meta = {
  name: '5plus2-run',
  description: 'Batch 5+2 fundamental deep-analysis. A first step screens a top-N book (or takes a watchlist), then per name runs the 7-step method — (1)industry (2)business-model (3)management (4)financials (5)valuation + (6)bull (7)risk — archetype-routed, ending with a rating card. The third analysis method alongside picks and portfolio.',
  phases: [
    { title: 'Screen', detail: 'top-N book (or supplied watchlist)' },
    { title: 'Analyze', detail: '7-step archetype-routed 5+2 card per name' },
  ],
}

const VENV = '/Users/ethanyang/clawd/.venv/bin/python'
const ENGINE = '/Users/ethanyang/Developer/github.com/YichengYang-Ethan/alpha-quant'
const ROUTER = `${ENGINE}/shared/archetype_router.py`   // factsheet + archetype + playbook in one call
const SCREEN = `${ENGINE}/shared/screen_book.py`
const N = (args && args.n) || 4   // 5+2 is heavy per name (web search + 7 steps); keep small
const SUPPLIED = (args && Array.isArray(args.tickers) && args.tickers.length) ? args.tickers : null

// ---- Phase 1: ticker source — supplied watchlist, else the deterministic screen ----
phase('Screen')
let tickers = SUPPLIED
if (!tickers) {
  const BOOK = {
    type: 'object', additionalProperties: false, required: ['book'],
    properties: { n: { type: 'number' }, book: { type: 'array', items: {
      type: 'object', additionalProperties: false, required: ['ticker'],
      properties: { ticker: { type: 'string' }, quant: { type: 'number' } } } } },
  }
  const s = await agent(
    `Run the deterministic screen and RETURN ITS JSON. Run exactly: ${VENV} ${SCREEN} --n ${N} --source sa\n` +
    `It prints {book:[{ticker,quant}], ...}. Return book.`,
    { label: 'screen', phase: 'Screen', schema: BOOK })
  tickers = ((s && s.book) || []).map((b) => b.ticker)
}
if (!tickers.length) { log('no tickers'); return { error: 'no tickers', method: '5plus2' } }
log(`5+2 deep-analysis on ${tickers.length}: ${tickers.join(', ')}`)

// ---- Phase 2: 7-step 5+2 per name (plain-text <note> card; no schema) ----
phase('Analyze')
const cards = await parallel(tickers.map((tk) => () =>
  agent(
    `Apply the "5+2" fundamental deep-analysis method to ${tk}. Seven steps: (1) industry (2) business model ` +
    `(3) management (4) financials (5) valuation — objective — then (6) bull case (7) risk — subjective.\n` +
    `STEP 1 — data + archetype: ${VENV} ${ROUTER} ${tk}\n` +
    `  Returns the factsheet (valuation/quality/growth/moat/statements/technicals/context) PLUS the routed archetype and ` +
    `its playbook (valuation method, financials focus, moat lens, bull template, risk clusters). USE the playbook to pick ` +
    `the right (4) financial metrics and (5) valuation method — do NOT put a bank on P/E, a story stock on relative ` +
    `multiples, or judge a membership retailer by gross margin. Confirm/override the archetype with judgment.\n` +
    `STEP 2 — if web search is available, look up (1) industry TAM + CAGR from a NAMED research firm (narrow definition), ` +
    `the competitive landscape, and industry-level risk; and (3) management (founder vs operator — judge by track record, ` +
    `not mechanically; any controversy). (2) moat, (4) financials, (5) valuation come from the factsheet/playbook.\n` +
    `STEP 3 — write the 5+2 card walking all 7 steps per the playbook, then a CONCLUSION: rating STRONG BUY / BUY / HOLD ` +
    `(≈ upside × conviction) + tier 1-4 (risk/certainty: 1=safest … 4=most speculative) + target-price range [bear, base, ` +
    `bull] (DCF base anchored below the analyst mean; target ∈ [base, bull]). Keep valuation ⊥ risk ((5) = cheap or not; ` +
    `(7) = safe to own or not — a name can be cheap AND high-risk). (7) MUST include a "paradigm shift" risk and the ` +
    `"the thing that made it succeed is its #1 risk" lens. End with the humble caveat: 5+2 is a starting point to ` +
    `understand a company, not a buy signal.\n` +
    `RULES: use ONLY the factsheet's real numbers (never invent grades or figures); ~250-350 words. ` +
    `Wrap ONLY the final 5+2 card in <note>...</note> tags (analysis may precede the tags). Do NOT call any tool to format it.`,
    { label: `5plus2:${tk}`, phase: 'Analyze' }
  ).then((t) => { const s = String(t || ''); const m = s.match(/<note>([\s\S]*?)<\/note>/i);
    return { ticker: tk, card: (m ? m[1] : s).trim() } }))
)

const ok = cards.filter((c) => c && c.card && c.card.length > 80)
log(`5+2: ${ok.length}/${tickers.length} cards`)
return {
  method: '5plus2', n: ok.length, source: SUPPLIED ? 'watchlist' : 'screen(top-N Strong-Buy)',
  cards: ok,
  note: '5+2 is an understanding framework (7 steps, archetype-routed), not a buy signal. Rating ⊥ tier = valuation (cheap or not) ⊥ risk (safe to own or not).',
}
