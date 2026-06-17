export const meta = {
  name: 'portfolio-run',
  description: 'Equal-weight Strong-Buy book builder. A first deterministic step screens the universe to a top-N equal-weight book, then writes a data-driven rationale per name. Self-wired (the screen agent runs the gate) — no external args, no file reads in JS. Distinct from the 2-pick funnel in alpha_run.js.',
  phases: [
    { title: 'Screen', detail: 'deterministic equal-weight Strong-Buy book' },
    { title: 'Buys', detail: 'rationale per equal-weight add' },
  ],
}

const VENV = '/Users/ethanyang/clawd/.venv/bin/python'
const ENGINE = '/Users/ethanyang/Developer/github.com/YichengYang-Ethan/alpha-quant'
const ANALYZE = `${ENGINE}/shared/alpha_analyze.py`
const SCREEN = `${ENGINE}/shared/screen_book.py`
const N = (args && args.n) || 12

// ---- Phase 1: the deterministic screen drives the book (no hardcoded list, no args needed) ----
phase('Screen')
const BOOK_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['n', 'weight_each', 'book'],
  properties: {
    n: { type: 'number' }, weight_each: { type: 'number' }, asof: { type: ['string', 'null'] },
    book: { type: 'array', items: {
      type: 'object', additionalProperties: false, required: ['ticker', 'quant'],
      properties: { ticker: { type: 'string' }, quant: { type: 'number' } } } },
  },
}
const screen = await agent(
  `Run the deterministic equal-weight Strong-Buy screen and RETURN ITS JSON VERBATIM as your structured output. ` +
  `Run exactly this one command (no edits):\n  ${VENV} ${SCREEN} --n ${N} --source sa\n` +
  `It prints {source, asof, n, weight_each, book:[{ticker,quant}]}. Return n, weight_each, asof, and book.`,
  { label: 'screen', phase: 'Screen', schema: BOOK_SCHEMA }
)
const book = (screen && Array.isArray(screen.book)) ? screen.book : []
if (!book.length) { log('screen returned an empty book'); return { error: 'empty screen', mode: 'equal-weight-book' } }
log(`screen -> ${book.length} names @ ~${(screen.weight_each * 100).toFixed(1)}% each (asof ${screen.asof}) -> ${book.map((b) => b.ticker).join(', ')}`)

// ---- Phase 2: one rationale per equal-weight add ----
phase('Buys')
// Buy rationales return PLAIN TEXT (no schema): "write the note" is a free-text task, and forcing a
// StructuredOutput call here made ~45% of agents fail (they wrote the prose, never called the tool).
const buys = await parallel(book.map((b) => () =>
  agent(
    `You are the analyst for an equal-weight, actively-rebalanced QUANT MODEL PORTFOLIO. ${b.ticker} is in the top-${book.length} ` +
    `Strong-Buy+floor book and is added as a ~${(screen.weight_each * 100).toFixed(1)}% equal-weight position.\n` +
    `STEP 1 — data package: ${VENV} ${ANALYZE} ${b.ticker} --source sa  (real quant + 5 factor grades V/G/P/M/R + factsheet + retrieved exemplars + honesty).\n` +
    `STEP 2 — write a tight weekly-note buy rationale (~120 words): lead with Market Cap + Quant Rating + Sector/Industry rank, ` +
    `then the business in a sentence and WHY the factor profile supports the add (walk the real grades; explain any weak grade — ` +
    `a soft Value grade is acceptable when Momentum+Revisions lead). Note one risk; use the package's exemplars to sanity-check.\n` +
    `RULES: use ONLY the package's real grades (never estimate); equal-weight ADD, not a concentrated bet. ` +
    `Wrap ONLY the final weekly note in <note>...</note> tags (analysis may come before the tags). Do NOT call any tool to format it.`,
    { label: `buy:${b.ticker}`, phase: 'Buys' }
  ).then((t) => { const s = String(t || ''); const m = s.match(/<note>([\s\S]*?)<\/note>/i);
    return { ticker: b.ticker, quant: b.quant, rationale: (m ? m[1] : s).trim() } }))
)

const ok = buys.filter((b) => b && b.rationale && b.rationale.length > 60)
log(`documented ${ok.length}/${book.length} adds`)
return {
  mode: 'equal-weight-book',
  source: 'sa', asof: screen.asof, n: book.length, weight_each: screen.weight_each,
  benchmark: 'equal-weight S&P (RSP)',
  new_buys: ok.map((b) => ({ ticker: b.ticker, quant: b.quant, rationale: b.rationale })),
  honesty: 'A single top-rated add is ~coin-flip vs the equal-weight benchmark (median slightly negative); the edge is the ' +
    'basket + cutting names that lose Strong-Buy fast while a few winners compound. Regime-dependent; gross of rebalance friction.',
}
