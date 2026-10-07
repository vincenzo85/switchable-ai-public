/* Regia del deck: numeri, navigazione, demo dal vivo / replay, vista relatore.
 *
 * Tasti: → spazio PgDn = avanti · ← PgUp = indietro · Home/End
 *        F schermo intero · P vista relatore · D demo dal vivo on/off
 *        B schermo nero · ? contatore FPS
 */
'use strict';

const API = 'http://127.0.0.1:8088';
const NUM = (window.NUMBERS || {}).numbers || {};
const missing = new Set();

// {{chiave}} → valore di numbers.json; una chiave sconosciuta è un errore visibile
function resolve(html) {
  return html.replace(/\{\{([\w.]+)\}\}/g, (_, k) => {
    if (!NUM[k]) { missing.add(k); console.error('numero senza fonte:', k); return `<span class="missing" data-missing="${k}">??${k}</span>`; }
    return `<span data-num="${k}" title="${NUM[k].label} — ${NUM[k].source}">${NUM[k].display}</span>`;
  });
}

function renderBars(root) {
  root.querySelectorAll('[data-bars]').forEach(el => {
    const cfg = JSON.parse(el.dataset.bars);
    const vals = cfg.rows.map(r => (NUM[r.key] ? Number(NUM[r.key].value) : 0));
    const ref = cfg.ref && NUM[cfg.ref.key];
    if (cfg.ref && !ref) missing.add(cfg.ref.key);
    const max = cfg.max || Math.max(...vals, ref ? Number(ref.value) : 0, 1e-9);
    const scale = v => Math.max(0.6, Math.min(78, (v / max) * 78));          // 22% riservato all'etichetta
    const refPct = ref ? scale(Number(ref.value)) : null;
    el.innerHTML = cfg.rows.map((r, i) => {
      const n = NUM[r.key], note = r.note && NUM[r.note];
      if (!n) missing.add(r.key);
      if (r.note && !note) missing.add(r.note);
      const pct = scale(vals[i]);
      const refLine = ref ? `<span class="ref" style="left:${refPct}%">${i === 0 ? `<b>${cfg.ref.label} <span data-num="${cfg.ref.key}">${ref.display}</span></b>` : ''}</span>` : '';
      return `<div class="bar" title="${r.name}: ${n ? n.display + ' — ' + n.source : '??'}"><span class="name" data-param>${r.name}</span>
        <span class="track"><span class="fill" style="width:${pct}%;background:${r.color || cfg.color || 'var(--ink)'};animation-delay:${i * 0.12}s"></span>${refLine}
        <span class="val" style="left:${pct}%"><span data-num="${r.key}">${n ? n.display : '??' + r.key}</span>${note ? ` <span class="note">· +<span data-num="${r.note}">${note.display}</span></span>` : ''}</span></span></div>`;
    }).join('');
  });
}

// ---------- costruzione delle slide ----------
const host = document.getElementById('slides');
STEPS.forEach((s, i) => {
  const wrap = document.createElement('div');
  wrap.innerHTML = resolve(s.html) + (s.cite ? `<p class="cite">${resolve(s.cite)}</p>` : '');
  const el = wrap.firstElementChild;
  if (s.cite) el.appendChild(wrap.querySelector('.cite'));
  el.dataset.step = i;
  host.appendChild(el);
});
renderBars(host);

// icone: <i data-ic="nome"> → SVG Lucide incorporato al build (offline)
const ICONS = window.ICONS || {};
host.querySelectorAll('[data-ic]').forEach(el => {
  const svg = ICONS[el.dataset.ic];
  if (!svg) { missing.add('icona:' + el.dataset.ic); console.error('icona mancante:', el.dataset.ic); return; }
  el.innerHTML = svg;
});

// fondali: se esiste talk/assets/img/<id>.* il build lo elenca in window.IMAGES
const IMAGES = window.IMAGES || {};
STEPS.forEach((st, i) => {
  const file = st.img && IMAGES[st.img.id];
  if (!file) return;
  const bg = document.createElement('div');
  bg.className = 'backdrop';
  bg.style.backgroundImage = `url("assets/img/${file}")`;
  host.children[i].prepend(bg);
  host.children[i].classList.add('has-img');
});
document.querySelectorAll('[data-event]').forEach(el => {
  const v = EVENT[el.dataset.event];
  if (el.dataset.event === 'repo') el.textContent = v || ''; else el.textContent = v || '—';
});
document.querySelectorAll('[data-meta]').forEach(el => { el.textContent = ((window.NUMBERS || {}).meta || {})[el.dataset.meta] || ''; });
if (missing.size) document.title = `⚠ ${missing.size} numeri senza fonte`;

// ---------- indicatore di volo: profilo di altitudine scalato sul tempo del talk ----------
const PHASES = [['boarding', 'Boarding'], ['briefing', 'Briefing'], ['gate', 'Gate'], ['decollo', 'Decollo'],
  ['crociera', 'Crociera'], ['turbolenza', 'Turbolenza'], ['atterraggio', 'Atterraggio'], ['arrivi', 'Arrivi']];
const Flight = (() => {
  const MINS = stepMinutes(window.BEATS || {});
  const dur = st => MINS[STEPS.indexOf(st)];
  const starts = []; let total = 0;
  STEPS.forEach(st => { starts.push(total); total += dur(st); });
  const span = {};
  STEPS.forEach((st, i) => {
    const sp = span[st.phase] || (span[st.phase] = { a: starts[i], b: starts[i] + dur(st) });
    sp.a = Math.min(sp.a, starts[i]); sp.b = Math.max(sp.b, starts[i] + dur(st));
  });
  const alt = t => {                                           // 0 = a terra, 1 = quota di crociera
    const d = span.decollo, c = span.crociera, tu = span.turbolenza, at = span.atterraggio;
    if (!d || t < d.a) return 0;
    if (t < d.b) return (t - d.a) / (d.b - d.a);
    if (c && t < c.b) return 1;
    if (tu && t < tu.b) return 1 - 0.09 * Math.abs(Math.sin((t - tu.a) * 5.5));
    if (at && t < at.b) return 1 - (t - at.a) / (at.b - at.a);
    return 0;
  };
  const X = t => 10 + (t / total) * 980, Y = t => 70 - alt(t) * 48;
  let d = '';
  for (let t = 0; t <= total + 1e-9; t += total / 400) d += (d ? 'L' : 'M') + X(t).toFixed(1) + ',' + Y(t).toFixed(1);
  const labels = PHASES.filter(([k]) => span[k]).map(([k, name]) => {
    const sp = span[k], mx = X((sp.a + sp.b) / 2), tiny = X(sp.b) - X(sp.a) < 70;   // fase corta: etichetta solo se corrente
    return `<line x1="${X(sp.a)}" x2="${X(sp.a)}" y1="74" y2="80" class="tick"/>` +
      `<text x="${mx}" y="94" class="ph${tiny ? ' tiny' : ''}" data-ph="${k}" text-anchor="middle">${name}</text>`;
  }).join('');
  const el = document.getElementById('flight');
  el.innerHTML = `<svg viewBox="0 0 1000 100" preserveAspectRatio="none" aria-hidden="true">
    <defs><clipPath id="flown"><rect id="flown-rect" x="0" y="0" width="0" height="100"/></clipPath></defs>
    <line x1="10" x2="990" y1="72" y2="72" class="ground"/>
    <path d="${d}" class="route-all"/><path d="${d}" class="route-flown" clip-path="url(#flown)"/>${labels}</svg>
    <div id="plane" title="">✈</div>`;
  const plane = document.getElementById('plane'), rect = document.getElementById('flown-rect');
  function show(i) {
    const st = STEPS[i], t = starts[i] + dur(st) / 2, x = X(t);
    rect.setAttribute('width', x);
    const slope = (Y(t + 0.2) - Y(t - 0.2)) / (X(t + 0.2) - X(t - 0.2) || 1);
    plane.style.left = `${x / 10}%`;
    plane.style.top = `${Y(t)}%`;
    plane.style.setProperty('--tilt', `${Math.atan(slope * 0.12) * 180 / Math.PI}deg`);
    plane.classList.toggle('shake', st.phase === 'turbolenza');
    el.querySelectorAll('.ph').forEach(p => p.classList.toggle('cur', p.dataset.ph === st.phase));
    el.dataset.phase = st.phase;            // in appendice l'indicatore si nasconde
  }
  return { show, total, span };
})();

// ---------- navigazione ----------
const slides = [...host.children];
let cur = -1, live = false, timers = [];
const chan = 'BroadcastChannel' in window ? new BroadcastChannel('sai-deck') : null;
const prog = document.getElementById('prog');

function clearTimers() { timers.forEach(clearTimeout); timers = []; }

function go(i) {
  i = Math.max(0, Math.min(STEPS.length - 1, i));
  if (i === cur) return;
  clearTimers();
  slides.forEach((el, k) => el.classList.toggle('on', k === i));
  cur = i;
  const [name, opts] = STEPS[i].scene;
  Engine.scene(name, opts);
  const SEQ = { demo: runDemo, stress: runStress, routing: runRouting, flow: runFlow, rag: runRag, boarding: runBoarding, finale: runFinale };
  if (SEQ[STEPS[i].enter]) SEQ[STEPS[i].enter]();
  prog.textContent = `${i + 1}/${STEPS.length}`;
  Flight.show(i);
  history.replaceState(null, '', `#${i + 1}`);
  chan && chan.postMessage({ type: 'state', i, live, at: Date.now() });
}

addEventListener('keydown', e => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const k = e.key;
  if (['ArrowRight', ' ', 'PageDown', 'Enter'].includes(k)) { e.preventDefault(); go(cur + 1); }
  else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); go(cur - 1); }
  else if (k === 'Home') go(0);
  else if (k === 'End') go(STEPS.length - 1);
  else if (k === 'f' || k === 'F') document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
  else if (k === 'p' || k === 'P') window.open('presenter.html', 'sai-presenter', 'width=1200,height=800');
  else if (k === 'b' || k === 'B') document.getElementById('black').classList.toggle('on');
  else if (k === 'd' || k === 'D') { live = !live; document.querySelectorAll('#mode').forEach(m => m.classList.toggle('on', live)); const i = cur; cur = -1; go(i); }
  else if (k === '?') document.getElementById('fps').classList.toggle('on');
  else if (k === 'a' || k === 'A') go(STEPS.findIndex(st => st.phase === 'appendice'));
});
addEventListener('click', e => { if (!e.target.closest('a,button,figure')) go(cur + (e.clientX > innerWidth / 3 ? 1 : -1)); });
chan && (chan.onmessage = m => { if (m.data.type === 'goto') go(m.data.i); if (m.data.type === 'hello') chan.postMessage({ type: 'state', i: cur, live }); });
setInterval(() => { document.getElementById('fps').textContent = `${Engine.fps.toFixed(0)} fps`; }, 500);

// ---------- demo "quattro destini": dal vivo se l'API risponde, altrimenti replay misurato ----------
const fmtEur = v => `€${v.toFixed(6)}`;
const fmtMs = v => (v >= 1000 ? `${(v / 1000).toFixed(1)} s` : `${v} ms`);
const ROUTE_LABEL = { local: 'Locale', cloud: 'Cloud', local_rag: 'RAG locale' };
const CARD_TITLE = ['ticket', 'analisi rischi', 'i nostri docs', 'riservato'];
const CARD_ICON = ['ticket', 'brain', 'book-open', 'lock'];

// replay: la latenza è il p50 misurato (numbers.json); dal vivo: i valori di questa esecuzione
function card(i, r, replay) {
  const fb = r.fallback ? `<span class="tag alert">fallback</span>` : '';
  const lat = replay ? resolve(`{{tco.task_${'abcd'[i]}.latency}}`) : fmtMs(r.latency_ms);
  const extra = replay ? '' : `\n${r.tokens_in}→${r.tokens_out} token · ${fmtEur(r.cost_eur)}`;
  return `<div class="panel demo-card" style="animation:flip .6s ${i * 0.15}s both"><i class="ic card-ic">${ICONS[CARD_ICON[i]] || ''}</i><p class="small">${CARD_TITLE[i]}</p>
    <p style="margin:1vh 0"><span class="route ${r.route}"><span>${ROUTE_LABEL[r.route]}</span></span> ${fb}</p>
    <pre>${r.model}\n<b class="lat">${lat}</b>${extra}</pre></div>`;
}

async function runDemo() {
  const box = document.getElementById('demo-cards'), note = document.getElementById('demo-note');
  const replay = window.REPLAY_DEMO || [];
  box.innerHTML = '';
  let useLive = false;
  if (live) {
    try { const r = await fetch(`${API}/health`, { signal: AbortSignal.timeout(2000) }); useLive = r.ok; } catch { useLive = false; }
  }
  note.textContent = useLive ? 'Dal vivo: API su questa macchina, Ollama locale, nessuna chiave cloud (il fallback è reale).'
    : 'Replay del run misurato (benchmarks/results/tco.json).';
  const totals = document.getElementById('demo-totals');
  if (totals) totals.style.visibility = useLive ? 'hidden' : 'visible';
  for (const [i, t] of replay.entries()) {
    let r = t;
    if (useLive) {
      try {
        const res = await fetch(`${API}/v1/ask`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: t.prompt_full || t.prompt, max_tokens: 120 }), signal: AbortSignal.timeout(90000) });
        const d = await res.json();
        r = { ...d.record, route: d.decision.route };
      } catch { r = t; }
    }
    if (STEPS[cur].enter !== 'demo') return;                    // l'oratore è già andato avanti
    box.insertAdjacentHTML('beforeend', card(i, r, !useLive));
    Engine.launch(r.route === 'cloud' ? 'cloud' : r.route, { bounce: r.fallback && r.route === 'cloud', speed: 0.01 });
    if (!useLive) await new Promise(ok => timers.push(setTimeout(ok, 900)));
  }
}

const at = (ms, fn) => timers.push(setTimeout(fn, ms));
const slideEl = () => slides[cur];

// ---------- WOW 1: le particelle della cabina costruiscono il biglietto ----------
function runBoarding() {
  at(2600, () => Engine.scene('pass', { dist: 4.6, dim: 0.35 }));        // il biglietto vero prende la scena
}

// ---------- WOW 2: la torre apre le piste e smista quattro richieste ----------
function runRouting() {
  const items = [...slideEl().querySelectorAll('#reqs li')];
  items.forEach(li => li.classList.remove('in'));
  const plan = [['local', {}], ['cloud', {}], ['local_rag', {}], ['cloud', { block: true, reason: 'RESIDENCY' }]];
  items.forEach((li, k) => at(+li.dataset.at, () => { li.classList.add('in'); Engine.launch(plan[k][0], { speed: 0.009, ...plan[k][1] }); }));
}

// ---------- una richiesta completa: lo schema si costruisce mentre il pacchetto viaggia ----------
function runFlow() {
  const parts = [...slideEl().querySelectorAll('.build > *')];
  parts.forEach(p => p.classList.remove('in'));
  parts.forEach((p, k) => at(300 + k * 260, () => p.classList.add('in')));
  at(300 + parts.length * 260, () => Engine.launch('local', { speed: 0.008 }));
}

// ---------- RAG: le domande scendono nella stiva, non volano fuori ----------
function runRag() {
  for (let k = 0; k < 6; k++) at(600 + k * 1400, () => Engine.launch('local_rag', { speed: 0.012 }));
}

// ---------- WOW 3: stress test, una rivelazione alla volta (replay del run misurato) ----------
function runStress() {
  const ev = window.REPLAY_STRESS || [];
  const root = slideEl(), $ = sel => root.querySelector(sel);
  ['.l-served', '.l-timeout', '.l-guard', '.l-final'].forEach(sel => $(sel).classList.remove('dim'));
  ['.l-timeout', '.l-guard', '.l-final'].forEach(sel => $(sel).classList.add('hidden'));
  $('.l-served').classList.remove('hidden');
  const c = { done: 0, fb: 0 };
  let guard = false;
  $('#c-done').textContent = '0'; $('#c-fallback').textContent = '0';
  const STEP = 120;
  ev.forEach((e, k) => at(500 + k * STEP, () => {
    if (e.status !== 'ok') return;
    c.done++; $('#c-done').textContent = c.done;
    if (e.fallback) { c.fb++; $('#c-fallback').textContent = c.fb; $('.l-timeout').classList.remove('hidden'); }
    if (!guard && (e.rules || []).includes('budget_guard')) {
      guard = true; $('.l-guard').classList.remove('hidden'); Engine.close('cloud', 'BUDGET');
    }
    Engine.launch(e.route, { bounce: e.fallback, speed: 0.024 });
  }));
  at(500 + ev.length * STEP + 900, () => {
    ['.l-served', '.l-timeout', '.l-guard'].forEach(sel => $(sel).classList.add('dim'));
    $('.l-final').classList.remove('hidden');
  });
}

// ---------- WOW 4: il volano accelera e collassa nella torre ----------
function runFinale() {
  at(300, () => Engine.scene('flywheel', { pitch: 0.4, dist: 5.2, fwSpeed: 0.006, orbiters: { local: 40, local_rag: 10, cloud: 12 } }));
  at(3300, () => Engine.scene('tower', { pitch: 0.42, dist: 5.6, spin: 0.05, lanes: ['local', 'cloud', 'local_rag'], reveal: [0, 350, 700], dim: 0.8 }));
  at(8600, () => Engine.scene('tower', { pitch: 0.42, dist: 7, spin: 0.02, dim: 0.15 }));   // torre spenta: resta la frase
}

go(Math.max(0, (parseInt(location.hash.slice(1), 10) || 1) - 1));
window.__deck = { go, get cur() { return cur; }, missing, total: STEPS.length, flight: Flight };
