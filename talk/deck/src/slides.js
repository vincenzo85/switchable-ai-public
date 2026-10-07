/* Le slide del talk — V3 "AI Traffic Control": una slide, una idea.
 *
 * Ogni slide ha un elemento visivo protagonista (3D, icona, numero gigante,
 * screenshot) e al massimo una frase breve: il resto è nelle speaker notes
 * (talk/CANOVACCIO.md). Ogni numero è un segnaposto {{chiave}} risolto da
 * talk/numbers.json al build (vietato scrivere cifre a mano: tests/test_deck.py).
 *
 * phase: fase del volo · beat: beat del canovaccio (più slide possono
 * dividersi un beat: il tempo si divide in parti uguali, salvo `min`)
 * scene: formazione 3D e stato delle rotte · enter: sequenza animata
 * img: l'immagine prevista (idea, prompt per la generazione, alternativa SVG/3D).
 *   Se esiste talk/assets/img/<id>.(webp|jpg|png) il deck la usa come fondale;
 *   altrimenti restano icone e 3D. L'elenco completo: talk/IMMAGINI.md.
 */
'use strict';

// gate: TODO speaker (sala). Il repo è privato fino alla mattina del talk (checklist del canovaccio)
const EVENT = { name: 'MLOps', date: '29 ottobre 2026', gate: '', repo: 'github.com/vincenzo85/switchable-ai-public' };
const TITLE = 'Non serve sempre un modello migliore. Serve una torre di controllo.';
const OFFICIAL = 'Architettura AI "Switchabile": Routing Dinamico, RAG Locale e Ottimizzazione TCO tra Cloud e On-Premise';
const IMG_STYLE = 'cinematic night photography, deep navy almost black background (#05060A), ivory highlights, ' +
  'accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left ' +
  'for a headline, 16:9, no text, no logos, no people faces';

const R = (route, label) => `<span class="route ${route}"><span>${label}</span></span>`;
const ic = (name, cls = '') => `<i class="ic ${cls}" data-ic="${name}" aria-hidden="true"></i>`;
const stat = (key, label) => `<div class="stat"><div class="big">{{${key}}}</div><div class="label">${label}</div></div>`;
const bars = (rows, opts = {}) => `<div class="bars" data-bars='${JSON.stringify({ rows, max: opts.max || null, color: opts.color || null, ref: opts.ref || null }).replace(/'/g, '&#39;')}'></div>`;
const kick = (phase, what) => `<p class="kicker"><span class="act">${phase}</span> · ${what}</p>`;
// tessera: icona grande, poche parole, un numero facoltativo
const tile = (icon, words, num = '', cls = '') => `<div class="tile ${cls}">${ic(icon)}<div class="tw">${num ? `<b class="big2">${num}</b>` : ''}<span>${words}</span></div></div>`;
// nodo di un flusso: icona sopra, una parola sotto
const node = (icon, word, cls = '') => `<span class="fnode ${cls}">${ic(icon)}<small>${word}</small></span>`;
const arrow = '<span class="farrow" aria-hidden="true">→</span>';

const STEPS = [
  // ───────────────────────── BOARDING
  { phase: 'boarding', beat: '0.1', title: 'Chi decide la rotta?', scene: ['cabin', { porthole: 1, dist: 4, dim: 0.9 }],
    img: { id: 'finestrino', idea: 'Finestrino di un aereo di notte, luci di una città lontana sotto, ala appena visibile.',
           prompt: `airplane window at night seen from the seat, distant city lights below, wing tip barely visible, ${IMG_STYLE}`,
           alt: '3D già presente: finestrino ovale con nuvole di particelle.' },
    html: `<div class="slide center cinema"><p class="beat"><em>Chi decide la rotta?</em></p></div>` },
  { phase: 'boarding', beat: '0.2', title: 'Un litro di latte', scene: ['cabin', { porthole: 0.55, dist: 4.4, dim: 0.5 }],
    img: { id: 'latte', idea: 'Una bottiglia di latte, sola, illuminata come un oggetto prezioso su un banco di minimarket notturno.',
           prompt: `a single glass bottle of milk on an empty corner-shop counter at night, dramatic spotlight, ${IMG_STYLE}`,
           alt: 'SVG: bottiglia stilizzata a linea avorio, contorno che si disegna.' },
    html: `<div class="slide center icon-slide"><div>${ic('milk', 'hero-ic')}<p class="beat">Un litro di latte.</p></div></div>` },
  { phase: 'boarding', beat: '0.2', title: 'Un jet', scene: ['cabin', { porthole: 0.3, dist: 4.6, dim: 0.4 }],
    img: { id: 'jet-parcheggio', idea: 'Un aereo di linea parcheggiato davanti a un minimarket di quartiere, scala assurda, notte.',
           prompt: `a huge airliner parked in a small neighbourhood corner-shop parking lot at night, absurd scale, wet asphalt reflections, ${IMG_STYLE}`,
           alt: '3D: particelle che formano la sagoma di un jet sopra il piazzale.' },
    html: `<div class="slide center icon-slide"><div>${ic('plane', 'hero-ic cloud-c')}<p class="beat">Un jet.</p></div></div>` },
  { phase: 'boarding', beat: '0.2', title: 'Anche quando basta camminare', scene: ['cabin', { porthole: 0, dist: 5, dim: 0.35 }],
    img: { id: 'passi', idea: 'Impronte di passi su un marciapiede bagnato che portano alla porta del negozio, a pochi metri.',
           prompt: `footprints on a wet sidewalk leading a few meters to a lit shop door at night, ${IMG_STYLE}`,
           alt: 'SVG: impronte che compaiono una alla volta.' },
    html: `<div class="slide center icon-slide"><div>${ic('footprints', 'hero-ic local-c')}<p class="beat"><em>Anche quando basta camminare.</em></p></div></div>` },
  { phase: 'boarding', beat: '0.3', title: 'La promessa: il boarding pass (WOW)', enter: 'boarding', scene: ['pass', { porthole: 0, dist: 4.6, dim: 0.75, yaw: 0, pitch: 0 }],
    img: { id: 'biglietto', idea: 'Nessuna foto: il biglietto è disegnato dalle particelle e poi appare in 3D.',
           prompt: '', alt: 'Già realizzato: formazione "pass" + card CSS 3D.' },
    html: `<div class="slide center cinema"><div class="pass reveal-late"><div class="card">
      <div class="main"><div class="f">Boarding pass · AI Traffic Control</div>
        <div class="title-line">${TITLE}</div>
        <div class="official">${OFFICIAL}</div>
        <div class="pax">${ic('users')}<span>CTO · MLOps · Architetti · FinOps · DPO · Dev</span></div></div>
      <div class="stub"><div><div class="f">Evento</div><div class="v" data-event="name">—</div></div>
        <div><div class="f">Data</div><div class="v" data-event="date">—</div></div>
        <div><div class="f">Gate</div><div class="v" data-event="gate">—</div></div></div></div></div></div>` },

  // ───────────────────────── BRIEFING
  { phase: 'briefing', beat: '1.1', title: 'Il patto: misurato, dichiarato, dal vivo', scene: ['airport', { pitch: 0.55, dist: 5.8, spin: 0.05, oy: 0.3, dim: 0.3 }],
    img: { id: 'patto', idea: 'Tre strumenti di bordo su un pannello di cockpit: un righello/scala, un documento timbrato, una spia rossa ON AIR.',
           prompt: `three glowing cockpit instruments side by side: a measuring gauge, a stamped checklist, a red ON AIR light, ${IMG_STYLE}`,
           alt: 'Icone (già presenti) che si accendono una alla volta.' },
    html: `<div class="slide center">${kick('Briefing', 'Il patto')}
      <div class="tiles three">${tile('ruler', 'Misurato')}${tile('file-check', 'Dichiarato')}${tile('radio', 'Dal vivo')}</div></div>` },
  { phase: 'briefing', beat: '1.1', title: 'Vi mostrerò un 96%. Non fidatevi.', scene: ['airport', { pitch: 0.55, dist: 6.4, spin: 0.04, oy: 0.34, dim: 0.2 }],
    img: { id: 'avviso', idea: 'Un cartello di avvertimento aeroportuale giallo, sfocato, "attenzione al gradino".',
           prompt: `a yellow airport caution sign out of focus in a dark terminal, single warm light, ${IMG_STYLE}`,
           alt: 'Icona triangolo di avviso che pulsa una volta.' },
    html: `<div class="slide center icon-slide"><div>${ic('triangle-alert', 'hero-ic warn-c')}
      <p class="beat">Vi mostrerò un {{tco.saving_energy_only}}.<br><em>Non fidatevi.</em></p></div></div>` },
  { phase: 'briefing', beat: '1.2', title: 'Quanto costa davvero un task?', scene: ['airport', { pitch: 0.5, dist: 5.4, spin: 0.05, ox: 0.3, dim: 0.35 }],
    img: { id: 'scontrino', idea: 'Uno scontrino lunghissimo che esce da una stampante, con righe di token invece di prodotti.',
           prompt: `an endless paper receipt curling out of a small printer in the dark, abstract lines instead of items, ${IMG_STYLE}`,
           alt: 'SVG: scontrino che si srotola, righe che compaiono.' },
    html: `<div class="slide center icon-slide"><div>${ic('receipt-euro', 'hero-ic')}<p class="beat">Quanto costa <em>davvero</em> un task?</p></div></div>` },

  // ───────────────────────── GATE
  { phase: 'gate', beat: '2.1', title: 'In produzione restano a terra', scene: ['airport', { pitch: 0.42, dist: 4.6, yaw: 0.5, spin: 0.05, dim: 0.25 }],
    img: { id: 'tabellone', idea: 'Tabellone partenze reale, tutto rosso: DELAYED/CANCELLED, aeroporto vuoto di notte.',
           prompt: `airport departures board at night with every flight marked delayed or cancelled in red and amber, empty terminal, ${IMG_STYLE}`,
           alt: 'Già realizzato: tabellone split-flap animato.' },
    html: `<div class="slide center"><div>${kick('Gate', 'Partenze')}
      <h1>In produzione <em>restano a terra.</em></h1>
      <div class="board icons" style="margin:4vh auto 0">
        <div class="row">${ic('wallet')}<span>Costi imprevedibili</span><span class="st flip">RITARDO</span></div>
        <div class="row">${ic('hourglass')}<span>Rate limit</span><span class="st flip">RITARDO</span></div>
        <div class="row">${ic('lock')}<span>Data residency</span><span class="st flip">BLOCCATO</span></div>
        <div class="row">${ic('eye-off')}<span>Costo per task ignoto</span><span class="st flip">RITARDO</span></div></div></div></div>`,
    cite: 'FrugalGPT (Chen, Zaharia, Zou 2023, arXiv:2305.05176): con una cascata di modelli, stessa qualità del migliore e {{lit.frugalgpt}} di costo.' },

  // ───────────────────────── DECOLLO
  { phase: 'decollo', beat: '3.1', title: 'Una riga', scene: ['pass', { dist: 6.5, dim: 0.25, oy: 0.1, yaw: 0, pitch: 0 }],
    img: { id: 'porta', idea: 'Una porta d\'imbarco chiusa con una sola luce sopra: dietro, rumore di motori diversi.',
           prompt: `a single closed boarding gate door with one light above it, hint of different aircraft silhouettes behind glass, ${IMG_STYLE}`,
           alt: 'SVG: una porta da cui escono tre linee colorate (locale/cloud/RAG).' },
    html: `<div class="slide center"><div>${kick('Decollo', 'Una porta, molti motori')}
      <h1>Una riga.</h1>
      <pre class="panel diff" style="margin-top:4vh"><span class="del">- base_url="https://api.openai.com/v1"</span>
<span class="add">+ base_url="http://localhost:8088/v1"</span></pre></div></div>` },
  { phase: 'decollo', beat: '3.2', title: 'Chi decide? (WOW: routing)', enter: 'routing',
    scene: ['tower', { pitch: 0.42, dist: 5.4, yaw: 0.35, lanes: ['local', 'cloud', 'local_rag'], reveal: [500, 1100, 1700], ox: 0.22 }],
    img: { id: 'torre', idea: 'Nessuna foto: è il momento del 3D (torre, tre piste che si aprono, quattro richieste).',
           prompt: '', alt: 'Già realizzato nel motore.' },
    html: `<div class="slide left"><div>${kick('Decollo', 'La torre')}
      <h1>Chi decide?</h1>
      <ol class="reqs icons" id="reqs">
        <li data-at="2600">${ic('ticket')}<span>Ticket</span> ${R('local', 'Locale')}</li>
        <li data-at="3500">${ic('brain')}<span>Analisi rischi</span> ${R('cloud', 'Cloud')}</li>
        <li data-at="4400">${ic('book-open')}<span>I nostri docs</span> ${R('local_rag', 'RAG')}</li>
        <li data-at="5300">${ic('lock')}<span>Riservato</span> <span class="tag alert">${ic('ban')} cloud</span> ${R('local', 'Locale')}</li></ol></div></div>` },
  { phase: 'decollo', beat: '3.3', title: 'La torre non è un LLM', scene: ['tower', { pitch: 0.4, dist: 5.4, spin: 0.06, lanes: ['local', 'cloud', 'local_rag'], closed: { cloud: 'RESIDENCY' }, dim: 0.35, ox: 0.28 }],
    img: { id: 'controllore', idea: 'Il controllore di volo umano davanti agli schermi radar, di spalle, regole scritte a pennarello sul vetro.',
           prompt: `an air traffic controller seen from behind in a dark tower cab, radar screens, rules handwritten on the glass, ${IMG_STYLE}`,
           alt: 'Icona robot barrato + torre 3D con la pista cloud sbarrata (già realizzato).' },
    html: `<div class="slide left icon-left"><div>${ic('bot-off', 'hero-ic alert-c')}<h1>La torre non è un LLM.</h1></div></div>`,
    cite: 'Rerouting LLM Routers (Shafran et al. 2025, arXiv:2501.01818): sequenze avversarie spingono un router "intelligente" verso il modello caro.' },
  { phase: 'decollo', beat: '3.3', title: 'Quattro regole dure', scene: ['tower', { pitch: 0.5, dist: 8.5, spin: 0.05, lanes: ['local', 'cloud', 'local_rag'], closed: { cloud: 'RESIDENCY' }, dim: 0.2, ox: 0.34, oy: 0.3 }],
    img: { id: 'regole', idea: 'Quattro cartelli aeroportuali luminosi in fila: lucchetto, casa, salvadanaio, cervello.',
           prompt: `four illuminated airport wayfinding signs in a row in a dark corridor, simple pictograms, ${IMG_STYLE}`,
           alt: 'Tessere-icona già presenti.' },
    html: `<div class="slide center">${kick('Decollo', 'Le regole dure')}
      <div class="tiles four">${tile('shield-check', 'Residency')}${tile('house', 'Solo locale')}${tile('piggy-bank', 'Budget')}${tile('brain', 'Complessità')}</div>
      <p class="msg">{{router.deterministic.latency}} aggiunti. Sabotate ogni notte.</p></div>` },

  // ───────────────────────── CROCIERA
  { phase: 'crociera', beat: '4.1', title: 'Una richiesta', enter: 'flow', scene: ['globe', { pitch: 0.25, dist: 7.5, spin: 0.08, dim: 0.35, oy: 0.3, arcs: ['local', 'cloud', 'local_rag'] }],
    img: { id: 'nastro', idea: 'Un nastro bagagli in un aeroporto vuoto con una sola valigia luminosa che viaggia.',
           prompt: `a single glowing suitcase travelling on an empty airport baggage conveyor at night, ${IMG_STYLE}`,
           alt: 'Già realizzato: lo schema si costruisce e un pacchetto viaggia sul globo.' },
    html: `<div class="slide top">${kick('Crociera', 'Il viaggio di una richiesta')}
      <div class="fflow build" style="margin-top:6vh">${node('smartphone', 'App')}${arrow}${node('radio-tower', 'Torre')}${arrow}${node('bot', 'Advisor')}${arrow}${node('minimize-2', 'Compressione')}${arrow}${node('route', 'Motore')}${arrow}${node('rotate-ccw', 'Fallback')}${arrow}${node('receipt-euro', 'Registro')}</div></div>` },
  { phase: 'crociera', beat: '4.2', title: 'Demo: quattro destini', enter: 'demo', scene: ['globe', { pitch: 0.25, dist: 6.6, spin: 0.1, oy: 0.26, arcs: ['local', 'cloud', 'local_rag'] }],
    img: { id: 'demo', idea: 'Nessuna foto: demo dal vivo sul globo.', prompt: '', alt: 'Già realizzato.' },
    html: `<div class="slide top"><div>${kick('Crociera', 'Dal vivo')} <span id="mode" class="tag live">dal vivo</span></div>
      <div class="grid4" id="demo-cards" style="margin-top:5vh"></div>
      <p class="small" id="demo-note" style="margin-top:2vh"></p></div>` },
  { phase: 'crociera', beat: '4.3', title: '96%', scene: ['globe', { pitch: 0.25, dist: 9, spin: 0.04, oy: 0.36, dim: 0.2 }],
    img: { id: 'novantasei', idea: 'Nessuna foto: il numero gigante da solo.', prompt: '', alt: '—' },
    html: `<div class="slide center cinema"><div><div class="giant">{{tco.saving_energy_only}}</div>
      <p class="beat" style="margin-top:2vh"><em>C'è qualcosa che non va.</em></p></div></div>` },
  { phase: 'crociera', beat: '4.4', title: 'La stiva', enter: 'rag', scene: ['globe', { pitch: 0.1, dist: 4.6, spin: 0.08, ox: 0.27, arcs: ['local_rag'] }],
    img: { id: 'stiva', idea: 'Stiva di un aereo cargo con scaffali di faldoni e una luce blu: i documenti restano a bordo.',
           prompt: `inside an aircraft cargo hold filled with neatly shelved document boxes, cold blue light, ${IMG_STYLE}`,
           alt: 'Già realizzato: le richieste entrano nel globo.' },
    html: `<div class="slide left icon-left"><div>${ic('book-open', 'hero-ic rag-c')}
      <h1>I documenti non escono.</h1>
      <div class="grid2 nums">${stat('rag.hit_at_3', `${ic('target')} fonte giusta`)}${stat('rag.answer_ok', `${ic('circle-check')} risposta giusta`)}</div></div></div>` },
  { phase: 'crociera', beat: '4.5', title: 'Una catena, non una chat', scene: ['globe', { pitch: 0.3, dist: 9, spin: 0.06, oy: 0.4, dim: 0.2 }],
    img: { id: 'catena', idea: 'Un nastro trasportatore notturno con documenti che passano sotto quattro stazioni luminose.',
           prompt: `an automated conveyor line at night passing documents under four glowing stations, industrial, ${IMG_STYLE}`,
           alt: 'Flusso di icone (già presente).' },
    html: `<div class="slide center">${kick('Crociera', "L'equipaggio · n8n")}
      <div class="fflow">${node('file-text', 'Documento')}${arrow}${node('tag', 'Classifica')}${arrow}${node('scissors', 'Estrai')}${arrow}${node('database', 'Indicizza')}${arrow}${node('clipboard-check', 'QA')}${arrow}${node('shield-check', 'Residency', 'ok')}</div>
      <div class="big3" style="margin-top:5vh">{{n8n.wall}}<small>a documento</small></div></div>` },
  { phase: 'crociera', beat: '4.5', title: 'Sabotaggi scoperti', scene: ['globe', { pitch: 0.3, dist: 6.4, spin: 0.08, oy: 0.32, dim: 0.3 }],
    img: { id: 'sabotaggio', idea: 'Un tecnico di notte che stacca un cavo in un hangar e una spia rossa che si accende subito.',
           prompt: `a night maintenance hangar, a hand unplugging a cable while a red warning light instantly turns on, ${IMG_STYLE}`,
           alt: 'Icona bug barrato con contatore.' },
    html: `<div class="slide center icon-slide"><div>${ic('bug-off', 'hero-ic')}
      <div class="giant mid">{{quality.mutation_killed}}/{{quality.mutation_total}}</div><p class="msg" style="margin-inline:auto">sabotaggi scoperti dai test</p></div></div>` },
  { phase: 'crociera', beat: '4.6', title: 'Il cockpit', scene: ['globe', { pitch: 0.2, dist: 6.5, spin: 0.05, dim: 0.2 }],
    img: { id: 'cockpit', idea: 'Screenshot vero di Grafana (già presente).', prompt: '', alt: 'Già realizzato.' },
    html: `<div class="slide top"><div>${kick('Crociera', 'Il cockpit')}<h1>Ogni token è un segnale.</h1></div>
      <figure class="shot" style="margin:4vh 0 0"><img src="assets/grafana-panels.png" alt="Grafana: costo cumulato reale contro tutto-cloud e turbolenza"></figure></div>` },
  { phase: 'crociera', beat: '4.6', title: 'La scatola nera', scene: ['globe', { pitch: 0.2, dist: 6.5, spin: 0.05, dim: 0.2 }],
    img: { id: 'scatola-nera', idea: 'La scatola nera arancione di un aereo, su un tavolo di laboratorio.',
           prompt: `an orange aircraft flight recorder black box on a dark lab table, single spotlight, ${IMG_STYLE}`,
           alt: 'Screenshot Langfuse (già presente) + icona euro.' },
    html: `<div class="slide center blackbox"><div>${kick('Crociera', 'La scatola nera')}
      <figure class="shot" style="margin:0 auto;max-width:86%"><img src="assets/langfuse-rows.png" alt="Langfuse: una trace per richiesta"></figure>
      <p class="beat" style="margin-top:4vh">$ ${ic('arrow-right')} ${ic('euro')}</p></div></div>` },
  { phase: 'crociera', beat: '4.7', title: 'Comprimere è buttare', scene: ['globe', { pitch: 0.2, dist: 7.5, spin: 0.06, dim: 0.25, oy: 0.3 }],
    img: { id: 'valigia', idea: 'Una valigia sottovuoto schiacciata con un passaporto lasciato fuori sul pavimento.',
           prompt: `a vacuum-compressed suitcase squeezed flat, a passport left behind on the floor next to it, ${IMG_STYLE}`,
           alt: 'Icona pacco + due numeri a confronto.' },
    html: `<div class="slide center">${kick('Crociera', 'Comprimere')}
      <div class="versus">${tile('target', 'decide la domanda', '{{compression.estrattiva_30.accuracy}}', 'good')}<span class="vs">vs</span>${tile('eye-off', 'alla cieca', '{{compression.agnostica_30.accuracy}}', 'warn')}</div></div>` },
  { phase: 'crociera', beat: '4.7', title: 'Il carico sceglie il motore', scene: ['globe', { pitch: 0.2, dist: 7.5, spin: 0.06, dim: 0.25, oy: 0.3 }],
    img: { id: 'motori', idea: 'Due motori d\'aereo sul banco prova: uno piccolo acceso, uno grande con tante bocchette.',
           prompt: `two jet engines on a test stand at night, one small, one large, heat haze, ${IMG_STYLE}`,
           alt: 'Icona tachimetro + numero.' },
    html: `<div class="slide center icon-slide"><div>${ic('gauge', 'hero-ic')}
      <div class="giant mid">{{vllm.speedup_batch}}</div><p class="msg" style="margin-inline:auto">vLLM sul batch · Ollama sulla singola richiesta</p></div></div>` },
  { phase: 'crociera', beat: '4.7', title: 'Due correzioni banali', scene: ['globe', { pitch: 0.2, dist: 7.5, spin: 0.06, dim: 0.25, oy: 0.3 }],
    img: { id: 'forbici', idea: 'Forbici che tagliano un faldone esattamente lungo i separatori di sezione.',
           prompt: `scissors cutting a thick binder exactly along its colored section dividers, top light, ${IMG_STYLE}`,
           alt: 'Icona forbici + numero.' },
    html: `<div class="slide center icon-slide"><div>${ic('scissors', 'hero-ic rag-c')}
      <div class="giant mid">{{rag.hit_at_3}}</div><p class="msg" style="margin-inline:auto">fonte giusta, dopo due correzioni</p></div></div>` },
  { phase: 'crociera', beat: '4.8', title: 'Il router perfetto non esiste', scene: ['tower', { pitch: 0.45, dist: 6, spin: 0.1, dim: 0.3, oy: 0.3 }],
    img: { id: 'radar', idea: 'Schermo radar con metà dei puntini dentro il bersaglio e metà fuori.',
           prompt: `a round radar screen where half of the blips land on target and half drift outside, green phosphor, ${IMG_STYLE}`,
           alt: 'Icona lista + numero.' },
    html: `<div class="slide center icon-slide"><div>${ic('list-checks', 'hero-ic')}
      <div class="giant mid">{{router.deterministic.heldout}}</div><p class="msg" style="margin-inline:auto">le regole, su richieste scritte con parole diverse</p></div></div>` },
  { phase: 'crociera', beat: '4.8', title: 'Un modello piccolo, ben istruito', scene: ['tower', { pitch: 0.45, dist: 6, spin: 0.1, dim: 0.3, oy: 0.3 }],
    img: { id: 'secondo-controllore', idea: 'Due postazioni in torre: un controllore e, accanto, una piccola console luminosa che suggerisce.',
           prompt: `two workstations in an air traffic control tower at night, one with a small glowing assistant console beside the main radar, ${IMG_STYLE}`,
           alt: 'Barre (già presenti).' },
    html: `<div class="slide top">${kick('Crociera', 'Il secondo controllore')}
      <div class="panel" style="margin-top:4vh;width:100%">${bars([
        { name: 'Regole', key: 'router.deterministic.heldout', note: 'router.deterministic.latency' },
        { name: 'Rizzo Flow 4B', key: 'router.rizzo.heldout', note: 'router.rizzo.latency' },
        { name: 'Rizzo, rotte descritte meglio', key: 'router.tuned.rizzo.test', note: 'router.tuned.rizzo.latency', color: '#199e70' }], { max: 1 })}</div></div>`,
    cite: 'The Routing Plateau (Lu et al. 2026, arXiv:2606.07587): i router convergono su un\'accuratezza simile, lontana dall\'ottimo.' },

  // ───────────────────────── TURBOLENZA
  { phase: 'turbolenza', beat: '5.1', title: 'Jet di cartone', scene: ['globe', { pitch: 0.25, dist: 9, spin: 0.2, shake: 0.6, oy: 0.34, dim: 0.5, arcs: ['local', 'cloud', 'local_rag'] }],
    img: { id: 'cartone', idea: 'Un modellino d\'aereo di cartone appeso a un filo davanti a un cielo dipinto.',
           prompt: `a cardboard model airplane hanging on a string in front of a painted stormy sky, theatre lighting, ${IMG_STYLE}`,
           alt: 'Icona aereo + scatola.' },
    html: `<div class="slide center icon-slide"><div><div class="icon-pair">${ic('plane', 'hero-ic cloud-c')}${ic('box', 'hero-ic')}</div>
      <p class="beat">Jet di cartone.</p><p class="simtag" style="margin-top:3vh" data-meta="cloud_simulation_note"></p></div></div>` },
  { phase: 'turbolenza', beat: '5.2', title: '100 richieste (WOW: turbolenza)', enter: 'stress', scene: ['globe', { pitch: 0.25, dist: 8.5, spin: 0.12, shake: 0.25, ox: 0.27, oy: 0.12, arcs: ['local', 'cloud', 'local_rag'] }],
    img: { id: 'turbolenza', idea: 'Nessuna foto: replay animato.', prompt: '', alt: 'Già realizzato.' },
    html: `<div class="slide top cinema">${kick('Turbolenza', 'Replay del run misurato')}
      <p class="simtag corner" data-meta="cloud_simulation_note"></p>
      <div class="stage" id="stress-stage">
        <p class="line l-served">${ic('activity', 'inline-ic')} <span class="counter-n" id="c-done">0</span></p>
        <p class="line l-timeout hidden">${ic('timer', 'inline-ic alert-c')} <b class="alert-txt">TIMEOUT</b> → ${R('local', 'locale')} <span class="counter-n" id="c-fallback">0</span></p>
        <p class="line l-guard hidden">${ic('ban', 'inline-ic alert-c')} <b class="alert-txt">BUDGET CLOUD</b></p>
        <div class="line l-final hidden">
          <p>${ic('circle-check', 'inline-ic local-c')} <b>{{stress.completed}}/{{stress.total_tasks}}</b></p>
          <p>${ic('shield-check', 'inline-ic local-c')} <b>{{stress.data_residency_violations}}</b> violazioni</p>
          <p>${ic('euro', 'inline-ic')} <b>{{stress.saving_pct}}</b></p></div></div></div>` },

  // ───────────────────────── ATTERRAGGIO
  { phase: 'atterraggio', beat: '6.1', title: 'Una GPU ferma costa più del cloud', scene: ['landing', { pitch: 0.3, dist: 4.2, ty: -0.4, dim: 0.3 }],
    img: { id: 'gpu-ferma', idea: 'Una scheda GPU spenta in un rack buio, coperta di polvere, con un cartellino del prezzo.',
           prompt: `an idle powered-off GPU card in a dark server rack with a hanging price tag, dust in the light beam, ${IMG_STYLE}`,
           alt: 'Icona CPU + pausa.' },
    html: `<div class="slide center icon-slide"><div><div class="giant mid"><s class="strike">{{tco.saving_energy_only}}</s></div>
      <div class="icon-pair">${ic('cpu', 'hero-ic')}${ic('pause', 'hero-ic alert-c')}</div>
      <p class="beat">Una GPU ferma costa più del cloud.</p></div></div>` },
  { phase: 'atterraggio', beat: '6.1', title: 'Il pareggio', scene: ['landing', { pitch: 0.3, dist: 4.2, ty: -0.4, dim: 0.3 }],
    img: { id: 'pareggio', idea: 'Una bilancia a due piatti in equilibrio: un chip da una parte, una nuvola dall\'altra.',
           prompt: `a balance scale in perfect equilibrium, a computer chip on one pan, a small cloud on the other, ${IMG_STYLE}`,
           alt: 'Barre con linea del cloud (già presenti).' },
    html: `<div class="slide top">${kick('Atterraggio', 'Il costo vero')}
      <div class="grid2" style="margin-top:4vh;grid-template-columns:1.5fr 1fr;width:100%"><div class="panel">${bars([
        { name: 'GPU al 5%', key: 'tco.amortized_eur_mtok_u5', color: '#199e70' },
        { name: 'GPU al 25%', key: 'tco.amortized_eur_mtok_u25', color: '#199e70' },
        { name: 'GPU all\'80%', key: 'tco.amortized_eur_mtok_u80', color: '#199e70' }], { ref: { key: 'tco.cloud_price_eur_mtok', label: 'cloud' } })}</div>
      <div class="tile big-tile">${ic('scale')}<div class="tw"><b class="big2">{{tco.breakeven_utilization}}</b><span>pareggio</span></div></div></div>
      <p class="small" style="margin-top:2vh">Ipotesi: {{tco.assumption}}</p></div>`,
    cite: 'Beyond Per-Token Pricing (Patil 2026, arXiv:2606.11690): una GPU sottoutilizzata può costare {{lit.patil}} per token.' },
  { phase: 'atterraggio', beat: '6.2', title: 'Ho trovato', scene: ['landing', { pitch: 0.3, dist: 4.2, ty: -0.4, dim: 0.3 }],
    img: { id: 'scoperte', idea: 'Una bacheca di sughero con quattro foto polaroid fissate con puntine.',
           prompt: `a cork board with four polaroid photos pinned on it, red string between them, dim light, ${IMG_STYLE}`,
           alt: 'Tessere-icona (già presenti).' },
    html: `<div class="slide center">${kick('Atterraggio', 'Ho trovato')}
      <div class="tiles four">${tile('gauge', 'utilizzo', '{{tco.breakeven_utilization}}')}${tile('list-checks', 'regole', '{{router.deterministic.heldout}}')}${tile('sparkles', 'piccolo modello', '{{router.tuned.rizzo.test}}')}${tile('shield-check', 'violazioni', '{{stress.data_residency_violations}}')}</div></div>` },
  { phase: 'atterraggio', beat: '6.2', title: 'Non dicono', scene: ['landing', { pitch: 0.3, dist: 4.2, ty: -0.4, dim: 0.3 }],
    img: { id: 'limiti', idea: 'Una mappa nautica con zone in bianco marcate "terra incognita".',
           prompt: `an old navigation chart with blank unmapped areas, a compass resting on it, low light, ${IMG_STYLE}`,
           alt: 'Tessere-icona (già presenti).' },
    html: `<div class="slide center">${kick('Atterraggio', 'Cosa non dicono')}
      <div class="tiles four muted">${tile('flask-conical', 'cloud simulato')}${tile('calculator', 'ipotesi hardware')}${tile('ruler', 'set piccoli')}${tile('laptop', 'una macchina')}</div></div>` },
  { phase: 'atterraggio', beat: '6.3', title: 'Ogni volo migliora il prossimo', scene: ['flywheel', { pitch: 0.55, dist: 4.8, ox: 0.27, orbiters: { local: 30, local_rag: 8, cloud: 10 } }],
    img: { id: 'volano', idea: 'Nessuna foto: il volano 3D con le tracce in orbita.', prompt: '', alt: 'Già realizzato.' },
    html: `<div class="slide left icon-left"><div>
      <h1>Ogni volo migliora il prossimo.</h1>
      <div class="tiles three compact" style="margin-top:4vh">${tile('database', 'esempi', '{{flywheel.exported}}')}${tile('eye-off', 'dati personali oscurati', '{{flywheel.pii_redactions}}')}${tile('graduation-cap', 'da insegnare al locale', '{{flywheel.distillation_candidates}}')}</div></div></div>`,
    cite: 'From Production Traffic to Post-Training (Tsymboi et al. 2026, arXiv:2609.01572): un modello addestrato sul proprio traffico serve il {{lit.flywheel}} delle richieste.' },
  { phase: 'atterraggio', beat: '6.4', title: 'Finale (WOW)', enter: 'finale', scene: ['flywheel', { pitch: 0.4, dist: 5.2, orbiters: { local: 40, local_rag: 10, cloud: 12 } }],
    img: { id: 'finale', idea: 'Nessuna foto: il volano collassa nella torre.', prompt: '', alt: 'Già realizzato.' },
    html: `<div class="slide center cinema finale"><div>
      <p class="word w1">Route.</p><p class="word w2">Measure.</p><p class="word w3">Improve.</p>
      <p class="beat tagline">Local when possible. Cloud when needed.<br><em>Observable always.</em></p></div></div>` },
  { phase: 'arrivi', beat: 'qa', title: 'Domande', min: 3, notes: 'Risposte di riserva e dettagli: appendice (tasto A, o clic sull\'elenco della vista relatore).', scene: ['landing', { pitch: 0.15, dist: 3.4, ty: -0.6, dim: 0.5 }],
    img: { id: 'arrivi', idea: 'La sala arrivi di notte, porte scorrevoli aperte, luce calda.',
           prompt: `airport arrivals hall at night, sliding doors open, warm light spilling out, empty, ${IMG_STYLE}`,
           alt: 'QR e titolo (già presenti).' },
    html: `<div class="slide center"><div><h1>Domande?</h1>
      <img class="qr" src="assets/qr-repo.svg" alt="QR del repository github.com/vincenzo85/switchable-ai-public"><p class="small" data-event="repo"></p></div></div>` },

  // ───────────────────────── APPENDICE (dopo il Q&A, fuori dal tempo del talk)
  { phase: 'appendice', beat: 'A.1', min: 0, title: 'Appendice · Per chi: i passeggeri', notes: 'Cosa porta a casa ciascun ruolo.', scene: ['airport', { pitch: 0.55, dist: 5.8, spin: 0.05, oy: 0.28, dim: 0.3 }],
    html: `<div class="slide top">${kick('Appendice', 'Per chi')}
      <div class="panel" style="margin-top:3vh;width:100%"><table>
        <tr><th>Chi</th><th>Cosa porta a casa</th></tr>
        <tr><td><b>CTO / CIO</b></td><td>costi prevedibili, niente lock-in: il fornitore si cambia dietro una riga di configurazione</td></tr>
        <tr><td><b>AI / ML lead, MLOps</b></td><td>routing misurabile, fallback, un registro per ogni chiamata</td></tr>
        <tr><td><b>Enterprise architect</b></td><td>un gateway OpenAI-compatible: le app esistenti non si riscrivono</td></tr>
        <tr><td><b>FinOps / CFO</b></td><td>costo per task e TCO ammortizzato, non il listino</td></tr>
        <tr><td><b>DPO e sicurezza</b></td><td>il dato sensibile non lascia la macchina, nemmeno verso l'osservabilità</td></tr>
        <tr><td><b>Sviluppatori</b></td><td>la stessa API di sempre, e un codice testato sabotandolo</td></tr></table></div></div>` },
  { phase: 'appendice', beat: 'A.2', min: 0, title: 'Appendice · Tecnologie e perché', notes: 'Lo stack completo con il motivo di ogni scelta.', scene: ['tower', { pitch: 0.5, dist: 6.4, spin: 0.06, dim: 0.2, oy: 0.1 }],
    html: `<div class="slide top">${kick('Appendice', 'Ogni strumento ha un perché')}
      <div class="grid2" style="margin-top:3vh;width:100%"><div class="panel"><table>
        <tr><th>Strumento</th><th>Perché questo</th></tr>
        <tr><td><b>LiteLLM</b></td><td>gateway OpenAI-compatible: alias, fallback, cento fornitori</td></tr>
        <tr><td><b>Ollama</b></td><td>modelli locali, il più veloce a richiesta singola</td></tr>
        <tr><td><b>vLLM</b></td><td>throughput sul batch (PagedAttention)</td></tr>
        <tr><td><b>FastAPI</b></td><td>la torre: API OpenAI-compatible, webhook, metriche</td></tr>
        <tr><td><b>n8n</b></td><td>workflow automatici senza codice nuovo</td></tr>
        <tr><td><b>MCP</b></td><td>gli agenti usano gli stessi strumenti</td></tr></table></div>
      <div class="panel"><table>
        <tr><th>Strumento</th><th>Perché questo</th></tr>
        <tr><td><b>hnswlib + nomic-embed</b></td><td>RAG tutto locale, leggero</td></tr>
        <tr><td><b>Langfuse</b></td><td>una trace per richiesta, self-hosted</td></tr>
        <tr><td><b>Prometheus + Grafana</b></td><td>il cockpit: costi e latenze nel tempo</td></tr>
        <tr><td><b>Docker Compose</b></td><td>tutto self-hosted e riproducibile</td></tr>
        <tr><td><b>Architettura esagonale</b></td><td>si cambiano i motori senza toccare le regole</td></tr>
        <tr><td><b>Rizzo Flow, Open-Jev</b></td><td>un secondo controllore che restituisce probabilità</td></tr></table></div></div></div>` },
  { phase: 'appendice', beat: 'A.3', min: 0, title: 'Appendice · Cosa dice la ricerca', notes: 'Mappa della letteratura: solo paper verificati, solo numeri presenti negli abstract.', scene: ['globe', { pitch: 0.2, dist: 8, spin: 0.05, dim: 0.25, oy: 0.36 }],
    html: `<div class="slide top">${kick('Appendice', 'Cosa dice la ricerca')}
      <div class="lit" style="margin-top:3vh">
        <div class="panel"><p class="kicker">Routing</p>
          <p><b class="big2">{{lit.frugalgpt}}</b> costo, stessa qualità<br><small>FrugalGPT · 2305.05176</small></p>
          <p><b class="big2">{{lit.routellm}}</b> senza perdere qualità<br><small>RouteLLM · 2406.18665</small></p>
          <p><b class="big2">{{lit.hybrid}}</b> chiamate al modello grande<br><small>Hybrid LLM · 2404.14618</small></p></div>
        <div class="panel"><p class="kicker">Limiti del routing</p>
          <p>I router convergono su un'accuratezza simile, lontana dall'ottimo<br><small>Routing Plateau · 2606.07587</small></p>
          <p>Sequenze avversarie spingono il router verso il modello caro<br><small>Rerouting LLM Routers · 2501.01818</small></p></div>
        <div class="panel"><p class="kicker">Economia</p>
          <p><b class="big2">{{lit.patil}}</b> penalità della GPU sottoutilizzata<br><small>Patil · 2606.11690</small></p>
          <p><b class="big2">{{lit.inference_econ}}</b> costo API con prompt caching<br><small>Inference Economics · 2607.13080</small></p></div>
        <div class="panel"><p class="kicker">Compressione e agenti</p>
          <p><b class="big2">{{lit.llmlingua}}</b> compressione con poca perdita<br><small>LLMLingua · 2310.05736</small></p>
          <p><b class="big2">{{lit.mcp_cli}}</b> il costo delle definizioni MCP<br><small>MCP vs CLI · 2608.08654</small></p>
          <p><b class="big2">{{lit.agent_tokens}}</b> token nei task agentici<br><small>2604.22750</small></p></div>
        <div class="panel"><p class="kicker">Flywheel</p>
          <p><b class="big2">{{lit.flywheel}}</b> del traffico servito dal modello addestrato in casa<br><small>Tsymboi et al. · 2609.01572</small></p></div></div>
      <p class="small" style="margin-top:2vh">Solo paper verificati e solo numeri presenti nell'abstract (docs/BIBLIOGRAFIA.md).</p></div>` },
  { phase: 'appendice', beat: 'A.4', min: 0, title: 'Appendice · MCP', notes: 'Se chiedono di MCP: sei tool, quanto pesano, perché tenerli corti.', scene: ['globe', { pitch: 0.2, dist: 5.6, spin: 0.14, ox: 0.29, arcs: ['local', 'cloud', 'local_rag'] }],
    html: `<div class="slide left"><div>${kick('Appendice', 'MCP: la porta laterale per gli agenti')}
      <h1>Un protocollo, gli stessi strumenti.</h1>
      <div class="grid2" style="margin-top:4vh">${stat('mcp.tools', 'tool esposti dal server MCP')}${stat('mcp.definition_tokens', 'il peso delle loro definizioni, a ogni richiesta')}</div>
      <p class="small" style="margin-top:3vh">Definizioni esaustive costano {{lit.mcp_cli}} (MCP vs CLI, arXiv:2608.08654): descrizioni corte.</p></div></div>` },
  { phase: 'appendice', beat: 'A.5', min: 0, title: 'Appendice · Ollama e vLLM', notes: 'Dettaglio del benchmark: stesso modello, quantizzazioni diverse.', scene: ['globe', { pitch: 0.2, dist: 6.2, spin: 0.08, dim: 0.3 }],
    html: `<div class="slide top">${kick('Appendice', 'Due motori locali')}
      <div class="grid2" style="margin-top:3vh"><div class="panel"><p class="small">Una richiesta alla volta (token/s)</p>${bars([
        { name: 'Ollama', key: 'vllm.ollama.c1.tps', color: '#3987e5' }, { name: 'vLLM', key: 'vllm.vllm.c1.tps', color: '#d95926' }])}</div>
      <div class="panel"><p class="small">Molte richieste insieme (token/s)</p>${bars([
        { name: 'Ollama', key: 'vllm.ollama.c16.tps', color: '#3987e5' }, { name: 'vLLM', key: 'vllm.vllm.c16.tps', color: '#d95926' }])}
        <p class="small" style="margin-top:1.4vh">Primo token: vLLM {{vllm.vllm.c16.ttft}} · Ollama {{vllm.ollama.c16.ttft}}</p></div></div>
      <div class="legend"><span><i style="background:#3987e5"></i>Ollama (GGUF Q4)</span><span><i style="background:#d95926"></i>vLLM (BF16, PagedAttention)</span><span>stesso modello, stessa GPU</span></div></div>` },
  { phase: 'appendice', beat: 'A.6', min: 0, title: 'Appendice · Compressione', notes: 'Dettaglio: guidata dalla domanda contro alla cieca.', scene: ['globe', { pitch: 0.2, dist: 6.2, spin: 0.08, dim: 0.3 }],
    html: `<div class="slide top">${kick('Appendice', 'Compressione')}
      <div class="grid2" style="margin-top:3vh">
        <div class="panel"><p class="kicker">Guidata dalla domanda</p><div class="big">{{compression.estrattiva_30.saving}}</div><div class="label">token in meno</div>
          <div class="big" style="margin-top:2vh;color:var(--local)">{{compression.estrattiva_30.accuracy}}</div><div class="label">risposte corrette</div></div>
        <div class="panel"><p class="kicker">Alla cieca</p><div class="big">{{compression.agnostica_30.saving}}</div><div class="label">token in meno</div>
          <div class="big" style="margin-top:2vh;color:#f0b429">{{compression.agnostica_30.accuracy}}</div><div class="label">risposte corrette</div></div></div>
      <p class="small" style="margin-top:2vh">Compito facile (un fatto da ritrovare). Senza compressione: {{compression.originale.accuracy}} corrette. Si comprime solo la rotta a pagamento.</p></div>`,
    cite: 'Cache-Aware Prompt Compression (Song 2026, arXiv:2607.15516): {{lit.capc}} di costo rispetto al prompt non compresso.' },
];

// minuti per step: `min` esplicito, altrimenti il beat del canovaccio diviso fra le slide che lo condividono
function stepMinutes(beats) {
  const share = {};
  STEPS.forEach(s => { if (s.min == null) share[s.beat] = (share[s.beat] || 0) + 1; });
  return STEPS.map(s => s.min ?? ((beats[s.beat] || {}).min ?? 1) / (share[s.beat] || 1));
}
