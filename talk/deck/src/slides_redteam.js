/* Deck RED TEAM — "Provo a far cadere la mia tesi".
 *
 * Deck separato dal talk principale, stesso motore e stessa estetica.
 * Metafora: la tesi attraversa dieci turbolenze (dieci attacchi di un CTO,
 * di un DPO, di un platform engineer). Per ogni attacco due slide: la
 * domanda ostile, poi la prova e la riformulazione (❌ → ✅).
 * In atterraggio: la tesi robusta.
 *
 * Fonti: solo paper VERIFICATO in docs/BIBLIOGRAFIA.md, solo numeri presenti
 * negli abstract (chiavi lit.*), più i nostri numeri misurati. Le funzioni di
 * LiteLLM citate sono verificate sulle release notes (v1.98–v1.103, ago–set 2026).
 * Ogni numero è un segnaposto {{chiave}} di talk/numbers.json.
 */
'use strict';

const EVENT = { name: 'MLOps', date: '29 ottobre 2026', gate: '', repo: 'github.com/vincenzo85/switchable-ai-public' };
const R = (route, label) => `<span class="route ${route}"><span>${label}</span></span>`;
const ic = (name, cls = '') => `<i class="ic ${cls}" data-ic="${name}" aria-hidden="true"></i>`;
const bars = (rows, opts = {}) => `<div class="bars" data-bars='${JSON.stringify({ rows, max: opts.max || null, color: opts.color || null, ref: opts.ref || null }).replace(/'/g, '&#39;')}'></div>`;
const kick = (phase, what) => `<p class="kicker"><span class="act">${phase}</span> · ${what}</p>`;
const tile = (icon, words, num = '', cls = '') => `<div class="tile ${cls}">${ic(icon)}<div class="tw">${num ? `<b class="big2">${num}</b>` : ''}<span>${words}</span></div></div>`;
const node = (icon, word, cls = '') => `<span class="fnode ${cls}">${ic(icon)}<small>${word}</small></span>`;
const arrow = '<span class="farrow" aria-hidden="true">→</span>';

// nel red team il 3D fa da sfondo: attenuato e in basso, mai sopra le parole
const calm = ([name, o]) => {
  const { lanes, arcs, reveal, closed, packets, ...rest } = o;   // niente piste/etichette: il contenuto è nell'HTML
  return [name, { ...rest, dim: Math.min(o.dim ?? 1, 0.25), dist: Math.max(o.dist ?? 5.2, 8), oy: 0.18, ox: 0 }];
};

// un attacco = due slide
const attack = (n, theme, icon, who, quote, scene, notes) => ({
  phase: 'turbolenza', beat: `T${n}a`, min: 0.9, title: `Attacco ${n} · ${theme}`, scene: calm(scene), notes,
  html: `<div class="slide center icon-slide attack"><div>${kick(`Attacco ${n}`, theme)}${ic(icon, 'hero-ic alert-c')}
    <p class="who">${ic('users', 'inline-ic')} ${who}</p><p class="beat quote">«${quote}»</p></div></div>`,
});
const answer = (n, theme, wrong, right, evidence, scene, notes, cite) => ({
  phase: 'turbolenza', beat: `T${n}b`, min: 1.1, title: `Risposta ${n} · ${theme}`, scene: calm(scene), notes, cite,
  html: `<div class="slide center">${kick(`Risposta ${n}`, theme)}
    <div class="rewrite"><p class="no">${ic('ban')} <s>${wrong}</s></p><p class="yes">${ic('circle-check')} ${right}</p></div>
    ${evidence ? `<div class="evidence">${evidence}</div>` : ''}</div>`,
});

const STEPS = [
  // ───────────────────────── BOARDING: la tesi da attaccare
  { phase: 'boarding', beat: 'R0', min: 0.8, title: 'Provo a far cadere la mia tesi', scene: ['cabin', { porthole: 1, dist: 4, dim: 0.9 }],
    notes: 'Questo deck è il red team del talk. Ho chiesto a un CTO ostile, a un DPO e a un platform engineer di smontarmi. Ecco dove ci sono riusciti.',
    html: `<div class="slide center cinema"><div><p class="kicker">Red team</p><p class="beat">Provo a far cadere<br><em>la mia tesi.</em></p></div></div>` },
  { phase: 'boarding', beat: 'R1', min: 1.0, title: 'La tesi da attaccare', scene: ['cabin', { porthole: 0.3, dist: 4.6, dim: 0.4 }],
    notes: 'La tesi nella versione che è facile demolire: routing cloud più locale riduce drasticamente i costi, aumenta la resilienza, protegge i dati e migliora da solo. Quattro promesse, quattro bersagli.',
    html: `<div class="slide center">${kick('La tesi', 'versione attaccabile')}
      <div class="tiles four claims">${tile('euro', 'riduce drasticamente i costi')}${tile('shield-check', 'protegge i dati')}${tile('refresh-ccw', 'aumenta la resilienza')}${tile('sparkles', 'migliora da solo')}</div></div>` },
  { phase: 'decollo', beat: 'R2', min: 0.7, title: 'Consente, non garantisce', scene: ['tower', { pitch: 0.45, dist: 6.5, spin: 0.06, dim: 0.3, oy: 0.3 }],
    notes: 'Il vero errore non è l\'architettura. È il verbo. Passo da "questa architettura consente X" a "garantisce X", e lì un CTO mi fa male. Il resto del deck è un elenco di quei passaggi.',
    html: `<div class="slide center"><div class="verbs"><p class="yes">consente</p><p class="no"><s>garantisce</s></p></div></div>` },

  // ───────────────────────── TURBOLENZA: dieci attacchi
  attack(1, 'Il TCO', 'hand-coins', 'CTO',
    'Hai trasformato una chiamata API in una piattaforma distribuita da mantenere.',
    ['landing', { pitch: 0.3, dist: 4.4, ty: -0.4, dim: 0.3 }],
    'LiteLLM, Ollama, vLLM, n8n, MCP, vector DB, Langfuse, Grafana, anonimizzazione, valutazione. Il TCO vero non è il costo per token: dentro ci sono persone, patching, incidenti, GPU ferme, storage, sicurezza, aggiornamento dei modelli, test di regressione e il costo dell\'errore.'),
  answer(1, 'Il TCO', 'abbattere il TCO', 'rendere il TCO misurabile, workload per workload',
    `<div class="tiles three compact">${tile('cloud', 'cloud con caching', '{{lit.inference_econ_cloud}}')}${tile('cpu', 'quota GPU locale condivisa', '{{lit.inference_econ_local}}')}${tile('bug', 'commit di riparazione col locale, contro {{lit.fcr_cloud}}', '{{lit.fcr_local}}', 'warn')}</div>`,
    ['landing', { pitch: 0.3, dist: 4.4, ty: -0.4, dim: 0.25 }],
    'Un paper che io stesso cito mi mette la mina sotto i piedi: con il prompt caching il cloud costa meno della quota locale ammortizzata, e il modello locale genera molto più lavoro di riparazione. Con la GPU dedicata il locale costa il 43,8% in più. Il mio pareggio al 12% conta energia e hardware, non le persone. Quindi non prometto un TCO più basso: prometto di poterlo misurare.',
    'Inference Economics of Enterprise Coding Agents (Peng, Lin, Lee 2026, arXiv:2607.13080): routing ibrido = frontiera costo-qualità, non dominanza; GPU dedicata {{lit.dedicated_more}}.'),

  attack(2, 'Il routing', 'route', 'ML platform engineer',
    'Come fai a sapere, prima dell\'inferenza, che una richiesta è semplice?',
    ['tower', { pitch: 0.42, dist: 5.6, spin: 0.08, lanes: ['local', 'cloud', 'local_rag'] }],
    '"Estrai il numero di fattura": sembra banale, poi arriva un PDF scansionato di 80 pagine. "Classifica questo ticket": sembra locale, ma descrive una vulnerabilità critica. La classe del task non è la difficoltà del task.'),
  answer(2, 'Il routing', 'regole deterministiche = routing corretto', 'policy first, learned routing second',
    `<div class="tiles three compact">${tile('list-checks', 'regole sulle parafrasi', '{{router.deterministic.heldout}}')}${tile('brain', 'complessi brevi riconosciuti', '{{router.deterministic.heldout_cloud}}', 'warn')}${tile('sparkles', 'piccolo modello, dentro le regole', '{{router.tuned.rizzo.test}}', 'good')}</div>`,
    ['tower', { pitch: 0.42, dist: 6.5, spin: 0.06, lanes: ['local', 'cloud', 'local_rag'], dim: 0.3, oy: 0.25 }],
    'Lo avevo già misurato: le regole fanno 53% sulle parafrasi e non riconoscono mai un compito difficile scritto corto. Anche LiteLLM nel 2026 non è più un router statico: ha un auto router euristico, un classificatore di capacità, shadow eval. La formulazione giusta: vincoli duri prima (privacy, budget, regione, strumenti), poi dentro lo spazio ammesso un router adattivo su costo, qualità, latenza e confidenza.',
    'LiteLLM release notes v1.98–v1.103 (ago–set 2026): heuristic auto router, capability classifier, auto-router shadow evals, Fuse routing.'),

  attack(3, 'I dati', 'lock', 'DPO',
    'Il documento resta locale. Ma il chunk che mandi al frontier model?',
    ['globe', { pitch: 0.2, dist: 6.4, spin: 0.08, oy: 0.25, arcs: ['local', 'cloud', 'local_rag'] }],
    'Documento locale, RAG, chunk, prompt al cloud: quella porzione non è più locale. Anche un riassunto può contenere dati personali o segreti industriali. E il GDPR non vieta il cloud extra-UE: esistono meccanismi e garanzie per i trasferimenti.'),
  answer(3, 'I dati', 'data residency totale', 'policy-enforced data locality: certe classi di dati non attraversano un certo confine di fiducia',
    `<div class="fflow">${node('file-text', 'Documento')}${arrow}${node('book-open', 'RAG locale', 'ok')}${arrow}${node('scissors', 'Chunk')}${arrow}${node('cloud-off', 'Confine di fiducia', 'stop')}</div>`,
    ['globe', { pitch: 0.2, dist: 7.5, spin: 0.06, oy: 0.32, dim: 0.4, arcs: ['local', 'cloud', 'local_rag'], closed: { cloud: 'TRUST BOUNDARY' } }],
    'Non prometto che i dati restano in casa: prometto una regola applicata. Una classe di dati, un confine di fiducia, e un controllo prima che il prompt lo attraversi, chunk compresi. Nel mio sistema la regola sui dati sensibili scatta sul prompt intero, non solo sul documento.',
    'EDPB, strumenti per i trasferimenti internazionali: il GDPR regola i trasferimenti extra-UE, non li vieta.'),

  attack(4, 'Il fallback', 'rotate-ccw', 'SRE',
    'Hai preservato lo stato. Hai preservato anche la capacità?',
    ['globe', { pitch: 0.25, dist: 6.4, spin: 0.1, shake: 0.3, oy: 0.25, arcs: ['local', 'cloud', 'local_rag'] }],
    'Passo da un frontier model a un 7B locale: posso trasferire tutta la conversazione e ottenere comunque una risposta peggiore.'),
  answer(4, 'Il fallback', 'il fallback mantiene il servizio', 'disponibilità, continuità e qualità sono tre metriche diverse',
    `<div class="tiles three compact">${tile('activity', 'disponibilità')}${tile('refresh-ccw', 'continuità del contesto', '{{lit.continuity}}')}${tile('target', 'qualità della risposta: da misurare', '', 'warn')}</div>`,
    ['globe', { pitch: 0.25, dist: 7.5, spin: 0.08, oy: 0.3, dim: 0.35, arcs: ['local', 'cloud', 'local_rag'] }],
    'ContinuityBench lo dice già nell\'abstract: alta disponibilità non significa continuità. E continuità non significa qualità. Nel mio stress test i fallback hanno sempre dato una risposta, ma la qualità di quelle risposte non l\'ho misurata. Questa può diventare una slide del talk principale.',
    'ContinuityBench (Pandey, Singh 2026, arXiv:2607.15899): {{lit.continuity}} di contesto preservato con failover stateful.'),

  attack(5, 'Lo stress test', 'activity', 'Reviewer',
    'Perché cento? Con quale concorrenza? E a diecimila?',
    ['globe', { pitch: 0.25, dist: 8, spin: 0.12, shake: 0.25, oy: 0.25, arcs: ['local', 'cloud', 'local_rag'] }],
    'Distribuzione dei task, concorrenza, timeout, quota locale e cloud, p95, saturazione della GPU, degradazione del provider o endpoint semplicemente spento: un "100 su 100" non risponde a nessuna di queste domande.'),
  answer(5, 'Lo stress test', '{{stress.completed}}/{{stress.total_tasks}}: il sistema è resiliente', 'controlled failure scenario, not a capacity benchmark',
    `<div class="tiles four compact">${tile('list-checks', 'richieste, una alla volta', '{{stress.total_tasks}}')}${tile('timer', 'latenza p95', '{{stress.latency_p95}}')}${tile('flask-conical', 'cloud simulato')}${tile('rotate-ccw', 'fallback', '{{stress.fallback_events}}')}</div>`,
    ['globe', { pitch: 0.25, dist: 8, spin: 0.08, oy: 0.3, dim: 0.35, arcs: ['local', 'cloud', 'local_rag'] }],
    'Il mio stress test è sequenziale, una richiesta alla volta, con un cloud simulato e una finestra di rallentamenti programmata. Dimostra che le regole reggono sotto guasto controllato. Non dice nulla sulla capacità. Lo scrivo sulla slide prima che me lo chiedano.'),

  attack(6, 'Il RAG', 'book-open', 'ML engineer',
    '{{rag.hit_at_3}} di accuratezza su quante domande?',
    ['globe', { pitch: 0.1, dist: 4.8, spin: 0.08, ox: 0.25, arcs: ['local_rag'] }],
    'Venti domande che funzionano dimostrano che quelle venti funzionano. E il RAG è una superficie d\'attacco nuova.'),
  answer(6, 'Il RAG', 'RAG accurato al {{rag.hit_at_3}}', 'recall@k, groundedness, abstention, su un set congelato, e un modello di minaccia',
    `<div class="tiles three compact">${tile('target', 'fonte giusta', '{{rag.hit_at_3}}')}${tile('list-checks', 'domande di riferimento', '{{rag.questions}}', 'warn')}${tile('shield-alert', 'avvelenamento distribuito su più documenti', '', 'warn')}</div>`,
    ['globe', { pitch: 0.1, dist: 6, spin: 0.06, ox: 0.25, dim: 0.35, arcs: ['local_rag'] }],
    'Il mio cento per cento è su sei domande. È un test di regressione, non una misura di accuratezza. E il controllo di pertinenza non basta contro l\'avvelenamento: c\'è un attacco che spezza il payload in passaggi innocui sparsi in più documenti.',
    'InceptionRAG (2026, arXiv:2609.16818): il payload frammentato in passaggi dormienti aggira le mitigazioni esistenti.'),

  attack(7, 'Il verifier', 'search', 'Platform engineer',
    'Il frontier model come fa a sapere che deploy-v1 è vecchio?',
    ['tower', { pitch: 0.42, dist: 6, spin: 0.08, lanes: ['local', 'cloud', 'local_rag'], dim: 0.4 }],
    'Se il RAG consegna un runbook vecchio, il modello grande non conosce la verità interna dell\'azienda. Può solo rendere più convincente la risposta sbagliata.'),
  answer(7, 'Il verifier', 'il frontier corregge il RAG rumoroso', 'un verifier ha bisogno di una fonte indipendente',
    `<div class="fflow">${node('book-open', 'RAG: deploy-v1', 'stop')}${arrow}${node('database', 'git HEAD: deploy-v4', 'ok')}${arrow}${node('clipboard-check', 'CI config: deploy-v4', 'ok')}${arrow}${node('badge-check', 'runbook firmato: deploy-v4', 'ok')}</div>`,
    ['tower', { pitch: 0.42, dist: 7, spin: 0.06, lanes: ['local', 'cloud', 'local_rag'], dim: 0.25, oy: 0.3 }],
    'Un modello che giudica un contesto che non può verificare non è un verifier. Il verifier confronta con fonti indipendenti: la HEAD di git, la configurazione della CI, un runbook firmato. Se tre dicono B e il RAG dice A, A si contesta.'),

  attack(8, 'Il flywheel', 'refresh-ccw', 'Data scientist',
    'Quindi addestri il modello sulle risposte dei modelli precedenti?',
    ['flywheel', { pitch: 0.55, dist: 4.8, ox: 0.25, orbiters: { local: 30, local_rag: 8, cloud: 10 } }],
    'Errori in produzione, dataset, fine-tuning, più errori. Bias di selezione: raccolgo solo i task che ricevo già. E un utente che non corregge non significa che la risposta sia giusta.'),
  answer(8, 'Il flywheel', 'traffico → fine-tuning', 'traffico → filtro → valutazione → etichette verificate → dataset curato → post-training → shadow → canary → produzione',
    `<div class="fflow small-flow">${node('activity', 'Traffico')}${arrow}${node('scissors', 'Filtro')}${arrow}${node('target', 'Valutazione')}${arrow}${node('badge-check', 'Etichette verificate', 'ok')}${arrow}${node('database', 'Dataset curato')}${arrow}${node('graduation-cap', 'Post-training')}${arrow}${node('eye-off', 'Shadow')}${arrow}${node('plane-takeoff', 'Canary')}</div>`,
    ['flywheel', { pitch: 0.55, dist: 6, orbiters: { local: 20, local_rag: 6, cloud: 8 }, dim: 0.4, oy: 0.3 }],
    'Il paper che cito arriva al 50% del traffico su 116 milioni di richieste al mese con analisi degli errori, benchmark rappresentativi della produzione, verifier deterministici o giudici calibrati e un training specifico. Non salvando i log e facendo una LoRA. Il mio flywheel oggi è solo il primo pezzo: filtro e anonimizzazione.',
    'From Production Traffic to Post-Training (Tsymboi et al. 2026, arXiv:2609.01572): {{lit.flywheel}} di {{lit.flywheel_volume}} richieste al mese, con analisi degli errori e verifier.'),

  attack(9, 'Il lock-in', 'plug', 'Enterprise architect',
    'Zero lock-in? Hai astratto l\'API, non il comportamento.',
    ['pass', { dist: 6.5, dim: 0.25, oy: 0.1, yaw: 0, pitch: 0 }],
    'Tool calling, output strutturati, contesto, controlli di ragionamento, multimodalità, semantica del caching, prompt di sistema, filtri, tokenizer, campionamento: tutto cambia da un modello all\'altro.'),
  answer(9, 'Il lock-in', 'zero vendor lock-in', 'meno lock-in di integrazione',
    `<div class="tiles three compact">${tile('plug', 'interfaccia portabile', '', 'good')}${tile('brain', 'comportamento da rivalidare', '', 'warn')}${tile('list-checks', 'test di regressione per ogni cambio di modello')}</div>`,
    ['pass', { dist: 7, dim: 0.2, oy: 0.1, yaw: 0, pitch: 0 }],
    'Cambiare una riga di base_url cambia l\'indirizzo, non il comportamento. La portabilità dell\'interfaccia non è portabilità del comportamento: ogni cambio di modello richiede la sua suite di regressione.'),

  attack(10, 'Il locale', 'cpu', 'CTO',
    'Perché locale? Davvero?',
    ['landing', { pitch: 0.3, dist: 4.4, ty: -0.4, dim: 0.3 }],
    'Per il costo? Un modello cloud economico può costare meno. Per la privacy? Ci sono cloud con regione europea. Per la latenza? Una GPU sottoutilizzata può essere peggio. Per la resilienza? Due fornitori cloud sono più facili di una GPU on-prem.'),
  answer(10, 'Il locale', "l'ibrido cloud + locale è la risposta", "l'ibrido non è un dogma: è un'opzione da misurare",
    `<div class="tiles four compact">${tile('euro', 'costo: un cloud economico')}${tile('shield-check', 'privacy: cloud in regione')}${tile('timer', 'latenza: GPU ferma')}${tile('cloud', 'resilienza: due fornitori')}</div>`,
    ['landing', { pitch: 0.3, dist: 4.4, ty: -0.4, dim: 0.25 }],
    'Ogni motivo per cui ho scelto il locale ha un\'alternativa cloud. E LiteLLM fa già routing su costo, latenza e limiti tra fornitori diversi. Il locale vince in alcuni workload e perde in altri: va misurato, non dato per scontato.'),

  // ───────────────────────── ATTERRAGGIO: la tesi robusta
  { phase: 'atterraggio', beat: 'R3', min: 1.2, title: 'Posso demolire la tesi? Sì.', scene: ['landing', { pitch: 0.3, dist: 4.2, ty: -0.4, dim: 0.3 }],
    notes: 'Sì. Il routing cloud più locale può costare di più, avere qualità inferiore, aprire nuove superfici d\'attacco, rendere l\'infrastruttura più complessa, creare dataset contaminati, far passare comunque dati sensibili, avere fallback riusciti sulla carta ma peggiori nei fatti, e aumentare il TCO operativo.',
    html: `<div class="slide center">${kick('Atterraggio', 'Sì, la tesi si può demolire')}
      <div class="tiles four compact fails">${tile('euro', 'costare di più')}${tile('target', 'qualità inferiore')}${tile('shield-alert', 'nuove superfici d\'attacco')}${tile('layers', 'più complessità')}${tile('database', 'dataset contaminati')}${tile('lock', 'dati che passano comunque')}${tile('rotate-ccw', 'fallback peggiori')}${tile('hand-coins', 'TCO operativo più alto')}</div></div>` },
  { phase: 'atterraggio', beat: 'R4', min: 1.5, title: 'La tesi robusta', scene: ['tower', { pitch: 0.42, dist: 5.6, spin: 0.05, lanes: ['local', 'cloud', 'local_rag'], reveal: [0, 350, 700], ox: 0.25 }],
    notes: 'La tesi che è difficile demolire: non esiste un modello o una strategia di deployment ottimale per tutti i workload. Serve un control plane che renda espliciti fiducia, qualità, costo e latenza, li misuri in produzione e scelga il compromesso giusto.',
    html: `<div class="slide left"><div>${kick('Atterraggio', 'La tesi robusta')}
      <p class="beat thesis">Non esiste un modello ottimale per tutti i workload.<br><em>Serve un control plane che li misuri e scelga il compromesso.</em></p>
      <div class="tiles four compact" style="margin-top:4vh">${tile('shield-check', 'fiducia')}${tile('target', 'qualità')}${tile('euro', 'costo')}${tile('timer', 'latenza')}</div></div></div>` },
  { phase: 'atterraggio', beat: 'R5', min: 0.8, title: 'Gli strumenti diventano la prova', scene: ['globe', { pitch: 0.25, dist: 7.5, spin: 0.06, dim: 0.3, oy: 0.3, arcs: ['local', 'cloud', 'local_rag'] }],
    notes: 'LiteLLM, il frontier, Ollama e vLLM, il RAG, Langfuse, Grafana, MCP e n8n non sono più la soluzione. Sono gli strumenti con cui dimostro la tesi.',
    html: `<div class="slide center">${kick('Atterraggio', 'Non la soluzione: la prova')}
      <div class="fflow">${node('radio-tower', 'Gateway')}${node('cloud', 'Frontier')}${node('cpu', 'Locale')}${node('book-open', 'RAG')}${node('activity', 'Tracce')}${node('chart-line', 'Metriche')}${node('plug', 'MCP')}${node('workflow', 'Workflow')}</div></div>` },
  { phase: 'atterraggio', beat: 'R6', min: 1.0, title: 'Anche il risultato negativo è un risultato', scene: ['landing', { pitch: 0.3, dist: 4.2, ty: -0.4, dim: 0.3 }],
    notes: '"In questo workload il locale perde contro il cloud." Perfetto: il sistema ha funzionato, perché lo ha misurato. È questa inversione che porta il talk da bella architettura self-hosted a tesi tecnica.',
    html: `<div class="slide center icon-slide"><div>${ic('scale', 'hero-ic')}<p class="beat">In questo workload il locale perde.<br><em>Il sistema ha funzionato: l'ha misurato.</em></p></div></div>` },
  { phase: 'arrivi', beat: 'R7', min: 3, title: 'Domande', scene: ['landing', { pitch: 0.15, dist: 3.4, ty: -0.6, dim: 0.5 }],
    notes: 'Il deck principale è il racconto; questo è il controesame. Le domande più dure sono benvenute.',
    html: `<div class="slide center"><div><h1>Attaccatemi.</h1>
      <img class="qr" src="assets/qr-repo.svg" alt="QR del repository github.com/vincenzo85/switchable-ai-public"><p class="small" data-event="repo"></p></div></div>` },
];

function stepMinutes() { return STEPS.map(s => s.min ?? 1); }
