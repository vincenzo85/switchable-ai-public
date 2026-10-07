# Canovaccio — Non serve sempre un modello migliore. Serve una torre di controllo.

> Il deck (`talk/deck`) legge da questo file, per ogni beat `## X.Y`, i tempi e le speaker notes: modificare qui, poi `make deck`.

**Titolo:** *Non serve sempre un modello migliore. Serve una torre di controllo.*
**Titolo ufficiale accettato (sempre visibile come sottotitolo):** Architettura AI "Switchabile": Routing Dinamico, RAG Locale e Ottimizzazione TCO tra Cloud e On-Premise.
**Concept visivo:** AI Traffic Control. **Evento:** MLOps · 29 ottobre 2026.

> **La sola frase da far ricordare:** non serve il modello migliore; serve mandare ogni richiesta sul modello giusto, sotto vincoli di costo, qualità e privacy, e sapere perché.
>
> **Il filo rosso (open loop):** nel briefing annuncio un risparmio del 96% {{tco.saving_energy_only}} e dico "non fidatevene"; lo mostro gigante dopo la demo; lo smonto in atterraggio con il TCO vero e il punto di pareggio al 12% {{tco.breakeven_utilization}}.
>
> **Durata: 30:00, Q&A compreso** — «[TODO organizzatori: confermare la durata dello slot]».

## Regole del canovaccio

- **Numeri**: solo da `talk/numbers.json`, sempre con la chiave: «€0.0011 {{tco.cost_real}}». Se un numero cambia si rigenera con `./run.sh numbers`; il test `tests/test_talk_numbers.py` segnala il testo rimasto vecchio.
- **Paper**: solo quelli VERIFICATO in `docs/BIBLIOGRAFIA.md`, solo con i numeri dell'abstract, uno per volta, accanto alla prova che sostengono. La mappa completa è in appendice (A.3).
- **Cloud simulato**: nello stress test il cloud è simulato e va detto a voce e scritto sulla slide, sempre.
- **Parlato**: affermazione → immagine mentale → prova → conseguenza. Mai "X fa questo, Y fa quello".
- **Quattro WOW, non quaranta**: boarding (0.3), routing (3.2), turbolenza (5.2), finale (6.4). Il resto è sobrio.
- **Tre modalità visive**: *cinema* (una frase, il 3D protagonista), *evidence* (un numero, una prova, una conclusione), *system* (un flusso costruito un pezzo alla volta).

## Cronometraggio

| Fase | Inizio–fine | Durata |
|---|---|---|
| BOARDING — rotta, provocazione, promessa | 00:00–02:30 | 2:30 |
| BRIEFING — il patto, il perché | 02:30–04:00 | 1:30 |
| GATE — perché l'AI resta a terra | 04:00–05:00 | 1:00 |
| DECOLLO — una riga, la torre, le regole | 05:00–08:15 | 3:15 |
| CROCIERA — richiesta, demo, 96%, prove, router | 08:15–17:10 | 8:55 |
| TURBOLENZA — annuncio e stress test | 17:10–20:10 | 3:00 |
| ATTERRAGGIO — twist, scoperte e limiti, loop, finale | 20:10–27:00 | 6:50 |
| ARRIVI — Q&A | 27:00–30:00 | 3:00 |
| **Totale** | | **30:00** |

---

# BOARDING · 00:00–02:30

## 0.1 · 00:00–00:30 · Chi decide la rotta?

**Modalità:** cinema. **Scena:** buio, un finestrino, nuvole che scorrono. Una sola frase: *Chi decide la rotta?*

**Speaker notes (parlato):**
> Silenzio per tre secondi. Poi: stamattina — «[TODO speaker: quando e da dove sei partito]» — ero seduto qui, vicino a un finestrino così. E mi sono chiesto: chi ha deciso la rotta di questo aereo? Non io. Non il pilota da solo. Una torre.

**Transizione:** «Ora immaginate di usare quell'aereo per comprare il latte.»

## 0.2 · 00:30–01:10 · Usiamo un jet anche quando basta camminare

**Modalità:** cinema. **Scena:** il finestrino si allarga. *Usiamo un jet anche quando basta camminare.*

**Speaker notes (parlato):**
> Un litro di latte al supermercato sotto casa. Invece di fare due passi, fate decollare un aereo di linea, atterrate nel parcheggio, caricate la bottiglia, ripartite. Ridete, ed è giusto. È quello che facciamo quando classifichiamo un ticket con il modello più grande e più caro che abbiamo.

**Transizione:** «Il problema non è il modello. È che nessuno decide il mezzo.»

## 0.3 · 01:10–02:30 · La promessa: il boarding pass

**Modalità:** cinema — **WOW 1**. **Scena:** le particelle della cabina convergono e disegnano un rettangolo; dentro appare il boarding pass 3D: titolo, titolo ufficiale sotto, *Route · Measure · Improve*, passeggeri *CTO · MLOps · Architetti · FinOps · DPO · Dev*, MLOps · 29 ottobre 2026.

**Speaker notes (parlato):**
> Oggi costruiamo una torre di controllo per l'AI. Il titolo ufficiale lo vedete sotto; quello vero è sopra: non serve sempre un modello migliore, serve una torre di controllo. Tre tappe: instradare, misurare, migliorare. E guardate i passeggeri: se siete un CTO vi porto a casa costi prevedibili; se fate MLOps un routing che si misura; se siete un DPO la garanzia che un dato sensibile non esce. In fondo al deck c'è il dettaglio per ciascuno.

**Transizione:** «Prima di salire, un patto.»

---

# BRIEFING · 02:30–04:00

## 1.1 · 02:30–03:15 · Il patto, e un numero da tenere a mente

**Modalità:** evidence. **Scena:** tre pannelli — Misurato · Dichiarato · Dal vivo — e sotto, grande, l'open loop.

**Numeri:** il 96% {{tco.saving_energy_only}} annunciato, non ancora spiegato.

**Speaker notes (parlato):**
> Un patto in tre parole. Misurato: ogni numero viene da un benchmark su questo portatile, con un file sorgente. Dichiarato: se c'è un'ipotesi o una simulazione, è scritta sulla slide. Dal vivo: la demo gira qui; se non risponde, ve lo dico e passo al replay. E vi faccio una promessa strana: tra poco vi mostrerò un risparmio del 96%. È vero. Prima di atterrare vi spiegherò perché non dovreste fidarvene.

**Transizione:** «Perché mi sono messo a fare tutto questo?»

## 1.2 · 03:15–04:00 · Perché l'ho costruito

**Modalità:** cinema. **Scena:** piazzale in penombra, una frase.

**Speaker notes (parlato):**
> Volevo sapere quanto costa davvero un task. Non il listino: il costo vero, su una macchina vera, con un fallback che scatta davvero. «[da confermare: il motivo personale — un conto cloud, una domanda di un cliente, un progetto]». Il primo prototipo l'ho scritto a luglio con una regola: niente slide-ware. Poi l'ho perso e l'ho ricostruito da un dump di testo. Questo è il secondo, e ogni numero ha una fonte.

**Transizione:** «Andiamo al gate, dove tanti voli restano fermi.»

---

# GATE · 04:00–05:00

## 2.1 · 04:00–05:00 · In demo vola tutto, in produzione gli aerei restano a terra

**Modalità:** cinema. **Scena:** il tabellone partenze: COSTI · RATE LIMIT · DATA RESIDENCY (BLOCCATO) · NESSUNA MISURA.

**Numeri:** FrugalGPT −98% {{lit.frugalgpt}} di costo a parità di qualità (citazione in basso).

**Speaker notes (parlato):**
> In demo vola tutto. In produzione gli aerei restano a terra, e quasi mai per colpa del modello. La bolletta cloud la scopri a fine mese. Il fornitore ti mette un rate limit. Certi documenti non possono uscire, punto. E nessuno sa quanto costa un singolo task, quindi nessuno lo ottimizza. Che non serva il modello più grande per tutto lo sappiamo dal 2023: FrugalGPT pareggiava il migliore spendendo fino al 98% in meno. Il problema è costruirlo in modo governabile.

**Transizione:** «Il decollo comincia cambiando una sola riga.»

---

# DECOLLO · 05:00–08:15

## 3.1 · 05:00–05:45 · Cambia una sola riga

**Modalità:** system. **Scena:** il biglietto si allontana; al centro un diff di due righe, enorme.

**Demo/log:** `infra/litellm.yaml` per tre secondi, se chiedono.

**Speaker notes (parlato):**
> Alla mia applicazione ho fatto credere di parlare sempre con la stessa API. Cambia una riga: l'indirizzo. Dietro quella porta posso cambiare motore senza che l'app se ne accorga: un gateway, modelli locali, il cloud quando serve. Da questo momento la domanda non è più "quale modello uso?". È "chi decide?".

**Transizione:** «Ecco chi decide.»

## 3.2 · 05:45–07:15 · La torre decide

**Modalità:** system — **WOW 2**. **Scena:** il biglietto si disintegra; le particelle costruiscono la torre; si aprono le tre piste — verde Locale, arancio Cloud, blu RAG. Arrivano quattro richieste: il ticket va sulla pista corta, l'analisi sul cloud, la domanda sui documenti nella stiva; il documento riservato punta il cloud, sbatte contro la barriera *CHIUSA · RESIDENCY* e ripiega sul locale.

**Speaker notes (parlato):**
> Guardate la torre. Classifica un ticket: pista corta, locale, quasi gratis. Analizza i rischi di una migrazione: serve ragionare, pista lunga, cloud. Come funziona il nostro fallback? È una domanda sulla nostra documentazione: non vola fuori, scende nella stiva. E poi un documento riservato chiede il cloud. La pista è chiusa. Non perché un modello l'ha deciso: perché c'è una regola. Torna indietro e atterra in locale.

**Transizione:** «Quella barriera è il cuore del design.»

## 3.3 · 07:15–08:15 · La torre non è un LLM

**Modalità:** evidence. **Scena:** la torre con la pista cloud sbarrata; la tabella delle quattro regole dure.

**Numeri:** le regole aggiungono 0 ms {{router.deterministic.latency}}.

**Speaker notes (parlato):**
> Mi chiedono: perché non fai decidere la rotta a un LLM? Tre motivi. Costa token e latenza a ogni richiesta; le regole aggiungono zero millisecondi. Non è prevedibile. E si può manipolare: c'è chi ha mostrato sequenze di token che spingono qualsiasi router verso il modello caro. Quindi prima le regole dure — dati sensibili, modalità locale, budget — e solo dopo l'intelligenza. E le regole le sabotiamo ogni notte, per vedere se i test se ne accorgono.

**Transizione:** «Siamo in quota. Seguiamo una richiesta dall'inizio alla fine.»

---

# CROCIERA · 08:15–17:10

## 4.1 · 08:15–09:15 · Una richiesta completa

**Modalità:** system. **Scena:** lo schema si costruisce un nodo alla volta mentre un pacchetto attraversa il globo: App → Torre → Advisor → Compressione → Locale/Cloud/RAG → Fallback → Registro costi.

**Speaker notes (parlato):**
> Un pacchetto. Arriva dall'app. La torre applica le regole dure. Se la regola non è sicura, chiede a un secondo controllore. Se la rotta costa, comprime il prompt. Chiama il motore; se cade, fallback; se la risposta locale non regge, escalation. E alla fine scrive una riga nel registro: token, costo, latenza, rotta. Il cuore che decide non sa nulla di rete né di fornitori: si cambia il motore, la regola resta.

**Transizione:** «Basta schemi. Dal vivo.»

## 4.2 · 09:15–11:00 · Demo: quattro richieste, quattro destini

**Modalità:** evidence. **Scena:** globo con i tre archi; per ogni richiesta parte un pacchetto e compare una card.

**Demo/log:** `./run.sh demo` (tasto D nel deck: dal vivo; altrimenti replay del run misurato).

**Numeri:** Task A 65 ms {{tco.task_a.latency}} · Task B 5.9 s {{tco.task_b.latency}} con fallback reale · Task C 5.5 s {{tco.task_c.latency}} · Task D 6.3 s {{tco.task_d.latency}} · fallback reali: 3 {{tco.fallbacks}}

**Speaker notes (parlato):**
> Lancio. Classificare un ticket: commuter, sessantacinque millisecondi. Analisi di rischio: la torre sceglie il jet, ma oggi il jet non ha carburante — non ho messo la chiave cloud — e guardate: ha risposto il locale. Il fallback non l'ho simulato, è successo. Domanda sul runbook: stiva, con le fonti. Documento riservato: resta a terra per regola.

**Transizione:** «E adesso il numero.»

## 4.3 · 11:00–11:30 · 96%: tenetelo a mente

**Modalità:** cinema. **Scena:** schermo quasi vuoto. Il numero, gigante.

**Numeri:** 96% {{tco.saving_energy_only}} · €0.0011 {{tco.cost_real}} contro €0.0256 {{tco.cost_if_cloud}}

**Speaker notes (parlato):**
> Novantasei per cento. Questo esperimento è costato il 96% in meno che mandare tutto in cloud. Pausa. Tenetelo a mente. C'è qualcosa che non va. Ci torniamo in atterraggio.

**Transizione:** «Intanto, la domanda sul runbook: dove è andata, esattamente?»

## 4.4 · 11:30–12:20 · La stiva: i documenti non escono

**Modalità:** evidence. **Scena:** le richieste non volano verso l'esterno: entrano dentro il globo, nella stiva.

**Numeri:** fonte giusta nei primi tre chunk 100% {{rag.hit_at_3}} · risposte con il dato atteso 83% {{rag.answer_ok}}

**Speaker notes (parlato):**
> Le domande sui nostri documenti non vanno in cloud: scendono nella stiva. Architettura, runbook, decisioni, perfino la storia git: tutto indicizzato qui. Guardate i due numeri separati. La fonte giusta arriva sempre. La risposta contiene il dato atteso quattro volte su cinque. Il recupero funziona; il modello piccolo, ogni tanto, risponde a modo suo. Si vede solo misurando.

**Transizione:** «La stiva però va riempita, e non a mano.»

## 4.5 · 12:20–13:20 · Dal chatbot al workflow

**Modalità:** system. **Scena:** documento → classifica → estrai → indicizza → checklist QA → residency ✓.

**Numeri:** 7.0 s {{n8n.wall}} a documento · 0 {{n8n.violations}} violazioni · 15 {{quality.mutation_killed}} sabotaggi su 15 {{quality.mutation_total}} scoperti

**Speaker notes (parlato):**
> Non sto costruendo una chatbot: sto costruendo una catena operativa. Arriva un documento, n8n chiama la torre quattro volte e il documento finisce indicizzato, con una checklist, in sette secondi. Il primo giro con dati veri ha trovato due bug del router che i miei test non vedevano. Li hanno fermati i test che ho scritto dopo, e ogni notte sabotiamo il codice per vedere se i test se ne accorgono: quindici su quindici. E gli agenti? Entrano da una porta laterale, un server MCP con gli stessi strumenti.

**Transizione:** «Tutto questo lascia una traccia.»

## 4.6 · 13:20–14:10 · Il cockpit

**Modalità:** evidence. **Scena:** Grafana (costo reale contro tutto-cloud, turbolenza) e tre righe di Langfuse.

**Speaker notes (parlato):**
> Quello che non misuri non puoi instradarlo. Grafana mi dice quanto costa davvero il traffico rispetto al tutto-cloud, e quanti fallback ci sono stati. Langfuse è la scatola nera: una traccia per volo. Se il dato è sensibile, la traccia arriva senza il contenuto. E una confessione: Langfuse scrive il simbolo del dollaro. Sono euro. Un dettaglio che in un report al CFO costa caro.

**Transizione:** «Misurando, ho dovuto cambiare idea su tre cose.»

## 4.7 · 14:10–15:40 · Tre cose che i benchmark mi hanno fatto cambiare

**Modalità:** evidence. **Scena:** tre pannelli, un numero grande ciascuno.

**Numeri:** compressione alla cieca 70% {{compression.agnostica_30.accuracy}} corrette contro 100% {{compression.estrattiva_30.accuracy}} guidate dalla domanda · vLLM 6.7× {{vllm.speedup_batch}} sul batch, ma a richiesta singola Ollama 175 tok/s {{vllm.ollama.c1.tps}} contro 75 tok/s {{vllm.vllm.c1.tps}} · RAG 100% {{rag.hit_at_3}} dopo due correzioni

**Speaker notes (parlato):**
> Credevo che comprimere i prompt fosse gratis. Comprimere è buttare informazione: se decide la domanda, perdo zero; se comprimo alla cieca, perdo un terzo delle risposte giuste. Credevo che vLLM fosse sempre più veloce: con una richiesta alla volta vince Ollama; con sedici richieste insieme vLLM fa quasi sette volte il throughput. Il carico sceglie il motore. E credevo che il RAG fosse una questione di modello: erano due correzioni banali, spezzare per sezione e usare i prefissi giusti.

**Transizione:** «La scoperta più grande però riguarda la torre stessa.»

## 4.8 · 15:40–17:10 · Il router perfetto non esiste

**Modalità:** evidence. **Scena:** la torre sullo sfondo; tre barre: regole, Rizzo Flow, Rizzo con le rotte descritte meglio.

**Numeri:** su 32 {{router.heldout_n}} richieste riscritte con parole diverse le regole fanno 53% {{router.deterministic.heldout}} e riconoscono i task complessi brevi nello 0% {{router.deterministic.heldout_cloud}} · Rizzo Flow 66% {{router.rizzo.heldout}} · con le rotte descritte meglio 78% {{router.tuned.rizzo.test}}, +90 ms {{router.tuned.rizzo.latency}} · descrizioni scelte su 42 {{router.dev_n}} richieste separate · in cloud senza motivo: 1 {{router.tuned.rizzo.cloud_errors}}

**Speaker notes (parlato):**
> Il numero che mi ha fatto più male. Sui casi che ho scritto io, le regole fanno cento per cento. Su trentadue richieste scritte con parole diverse, cinquantatré. Sbagliano sempre verso il risparmio — mai in cloud per errore — ma un compito difficile scritto in poche righe non lo riconoscono mai. Ho messo accanto un secondo controllore, un modello piccolo locale: sessantasei. Poi ho fatto la cosa noiosa e giusta: altre quarantadue richieste separate, e solo su quelle ho descritto meglio le piste. Misurato una volta sola: settantotto, novanta millisecondi, una richiesta in cloud senza motivo su trentadue. Il router perfetto non esiste; quello misurato sì. E le regole dure restano sopra.

**Transizione:** «Fin qui il volo è stato regolare.»

---

# TURBOLENZA · 17:10–20:10

## 5.1 · 17:10–17:40 · Annuncio dal comandante: il cloud è simulato

**Modalità:** cinema. **Scena:** il globo trema; cartello giallo con la dichiarazione di simulazione.

**Speaker notes (parlato):**
> Annuncio del comandante. Nel test che state per vedere il jet è di cartone: quando la torre manda una richiesta in cloud, risponde un modello locale, pagato a listino, e alcune chiamate sono rallentate apposta. Il routing, le regole, il budget, i fallback e il registro sono veri.

**Transizione:** «Cento richieste. Il sistema deve sopravvivere.»

## 5.2 · 17:40–20:10 · Stress test: 100 richieste

**Modalità:** cinema — **WOW 3**. **Scena:** replay del run misurato. Il contatore sale; poi *TIMEOUT → locale*; poi la pista cloud si chiude: *BUDGET CLOUD CHIUSO*; alla fine, tre righe: servite, violazioni di privacy, costo.

**Numeri:** 100 {{stress.completed}} su 100 {{stress.total_tasks}} servite · 4 {{stress.fallback_events}} timeout ripresi in locale · 0 {{stress.data_residency_violations}} violazioni di privacy · 82% {{stress.saving_pct}} di costo contro tutto-cloud · eseguite davvero in cloud: 11 {{stress.executed.cloud}}

**Speaker notes (parlato):**
> Cento richieste: ticket, estrazioni, analisi, domande sui documenti, dati sensibili. Guardate i pacchetti. Arriva la turbolenza: quattro chiamate al cloud vanno in timeout, tornano indietro e atterrano in locale; l'utente ha comunque una risposta. Poi il budget del giorno finisce: la pista cloud si chiude, e i task complessi restano a terra, peggiori ma dentro il budget. Fine. Cento su cento servite. Zero violazioni di privacy. Ottantadue per cento in meno. Che è meno del novantasei di prima, perché qui il jet ha volato davvero, undici volte.

**Transizione:** «Siamo atterrati. E adesso quel novantasei.»

---

# ATTERRAGGIO · 20:10–27:00

## 6.1 · 20:10–22:10 · Il twist: una GPU ferma costa più del cloud

**Modalità:** evidence. **Scena:** il 96% compare e viene barrato. Barre del costo locale ammortizzato con la linea di riferimento del cloud; a destra, grande, il pareggio.

**Numeri:** 96% {{tco.saving_energy_only}} barrato · cloud €4.60/Mtok {{tco.cloud_price_eur_mtok}} · locale con GPU al 5% €10.41/Mtok {{tco.amortized_eur_mtok_u5}} · all'80% €0.91/Mtok {{tco.amortized_eur_mtok_u80}} · pareggio 12% {{tco.breakeven_utilization}} · ipotesi 2000 € di hardware, 36 mesi, 140 W, 0,30 €/kWh {{tco.assumption}} · throughput misurato 42 tok/s {{tco.local_tps}}

**Speaker notes (parlato):**
> Vi avevo chiesto di ricordarlo: novantasei per cento. È vero, ed è una tautologia. Se dico che il locale costa solo l'elettricità, il risparmio è il rapporto tra due listini: esce sempre uguale, qualunque cosa faccia il sistema. Il costo vero include la macchina. Con un'ipotesi dichiarata — duemila euro, tre anni, centoquaranta watt — e un throughput misurato qui: se la GPU lavora il cinque per cento del tempo, il commuter costa più del doppio del cloud. All'ottanta per cento costa un quinto. Il pareggio è intorno al dodici per cento. La domanda giusta non è "cloud o on-premise". È: quanto lavoro ho da dare a questa macchina? E il routing serve anche a riempirla.

**Transizione:** «Ecco cosa ho trovato, e cosa questi numeri non dicono.»

## 6.2 · 22:10–23:40 · Cosa ho trovato, e cosa questi numeri non dicono

**Modalità:** evidence. **Scena:** due colonne: *Ho trovato* · *Non dicono*.

**Numeri:** pareggio 12% {{tco.breakeven_utilization}} · regole 53% {{router.deterministic.heldout}}, modello piccolo ben istruito 78% {{router.tuned.rizzo.test}} · sotto stress 4 {{stress.fallback_events}} fallback e 0 {{stress.data_residency_violations}} violazioni · set di prova di 42 {{router.dev_n}} e 32 {{router.heldout_n}} richieste

**Speaker notes (parlato):**
> Ho trovato quattro cose. Il risparmio dipende dall'utilizzo, non dal modello. Le regole non bastano, e un modello piccolo ben istruito le aiuta. Sotto stress il sistema non tradisce le regole. E i bug veri li trovano i dati veri. Ma siate severi con me: nello stress il cloud era simulato; il TCO usa un'ipotesi hardware mia; i set di prova sono piccoli e li ho scritti io; è una sola macchina con modelli da sette miliardi, e il flywheel non ha ancora addestrato niente. Rifatelo sulla vostra macchina: i numeri cambieranno, il metodo no.

**Transizione:** «Resta l'ultima tappa del piano di volo: migliorare.»

## 6.3 · 23:40–24:40 · Il loop: ogni trace migliora il prossimo volo

**Modalità:** cinema. **Scena:** le richieste diventano punti colorati che orbitano nel volano.

**Numeri:** 49 {{flywheel.exported}} esempi esportati · 4 {{flywheel.pii_redactions}} dati personali oscurati · 10 {{flywheel.distillation_candidates}} risposte cloud da insegnare al locale · in letteratura: un modello addestrato sul proprio traffico serve il 50% {{lit.flywheel}} delle richieste

**Speaker notes (parlato):**
> Le richieste di prima non sono sparite: girano qui. Il flywheel pulisce le tracce, oscura i dati personali, e mette da parte le risposte del jet come esempi per insegnare al commuter. C'è chi l'ha portato in produzione: un modello addestrato sul proprio traffico che serve metà delle richieste di un'azienda. Più il commuter impara, più lavoro gli date. Più lavoro, più utilizzo. E sapete cosa succede al TCO quando sale l'utilizzo.

**Transizione:** «Guardate il volano.»

## 6.4 · 24:40–27:00 · Finale: il volano collassa nella torre

**Modalità:** cinema — **WOW 4**. **Scena:** il volano accelera e collassa nella torre; si accendono le tre piste; appaiono *Route. Measure. Improve.*; le parole spariscono, la torre si spegne, resta la tagline.

**Speaker notes (parlato):**
> (Lasciate girare il volano, in silenzio.) Route: una torre tra le app e i modelli, con regole che non si negoziano. Measure: il costo vero, non il rapporto tra due listini. Improve: ogni traccia è un dato per il prossimo modello. Per venire qui ho preso «[TODO speaker: mezzo per l'aeroporto]», poi l'aereo, e l'ultimo tratto l'ho fatto «[TODO speaker: a piedi / in metro]». Nessuno mi ha chiesto perché non ho preso l'aereo per attraversare la strada: vedo costo e distanza. Con l'AI non è ovvio solo perché non lo misuriamo. Local when possible. Cloud when needed. Observable always. Grazie.

**Transizione:** «Le domande sono la parte del volo che preferisco.» → Q&A.

---

# ARRIVI — Q&A · 27:00–30:00

**Scena visiva:** titolo, QR del repository (github.com/vincenzo85/switchable-ai-public). Dalla vista relatore si salta a qualsiasi slide; il tasto **A** porta all'appendice.

# APPENDICE (fuori dal tempo del talk)

Si raggiunge dal Q&A con il tasto A o dall'elenco della vista relatore.

- **A.1 Per chi** — tabella dei sei ruoli e cosa porta a casa ciascuno.
- **A.2 Tecnologie e perché** — LiteLLM, Ollama, vLLM, FastAPI, n8n, MCP, hnswlib + nomic-embed, Langfuse, Prometheus + Grafana, Docker Compose, architettura esagonale, Rizzo Flow / Open-Jev.
- **A.3 Cosa dice la ricerca** — mappa in cinque rotte: routing (FrugalGPT −98% {{lit.frugalgpt}}), limiti del routing, economia (Patil fino a 24× {{lit.patil}}), compressione e agenti (LLMLingua fino a 20× {{lit.llmlingua}}), flywheel (50% {{lit.flywheel}}).
- **A.4 MCP** — sei tool, il peso delle definizioni.
- **A.5 Ollama e vLLM** — il benchmark completo.
- **A.6 Compressione** — guidata contro alla cieca.

# Pitch di 60 secondi

> Usiamo un jet anche quando basta camminare: il modello più grande per ogni richiesta, anche la più banale. In questo talk costruisco dal vivo una torre di controllo per l'AI, su un portatile, in Docker: una riga di `base_url`, poi la torre manda ogni richiesta sulla pista giusta — locale, cloud o la stiva dei documenti — con regole che nessun modello può scavalcare. Vi mostro un risparmio del 96% e vi chiedo di non fidarvi. Poi cento richieste in turbolenza, con un cloud simulato e dichiarato: timeout ripresi, budget che chiude la pista, zero violazioni di privacy. E alla fine il numero vero: una GPU ferma costa più del cloud, e il pareggio è all'utilizzo, non al modello. Local when possible. Cloud when needed. Observable always.

# Rischi live e piano B

Regola generale: **ogni demo ha uno screenshot o un replay pronto nella slide successiva**. Se una demo non risponde entro 10 secondi, si dice "la turbolenza è vera" e si passa al replay. Il deck ha un replay registrato e un PDF di riserva «[TODO speaker: percorso del PDF di riserva e della registrazione video, su chiavetta e in locale]».

| Rischio | Sintomo | Piano B |
|---|---|---|
| **Rete assente o lenta in sala** | nessuno, per scelta: la demo gira tutta in locale e senza chiave cloud | Nessuna dipendenza da rete. Non fare `docker pull` in sala. Se serve internet per il QR, mostrarlo come immagine. |
| **GPU non disponibile / driver** | Ollama gira su CPU, latenze di decine di secondi | Saltare `./run.sh demo` e mostrare l'output registrato (`benchmarks/results/tco.json`, stessi numeri della slide); dire apertamente "la GPU stamattina ha deciso di restare in hangar". |
| **Docker non parte** (LiteLLM, Langfuse, Grafana, n8n) | `./run.sh up` fallisce o i container non sono healthy | La demo 4.2 funziona anche senza gateway (`SAI_GATEWAY_URL` vuoto: si parla direttamente a Ollama). Cockpit e n8n: usare `talk/assets/grafana-cockpit.png` e `talk/assets/langfuse-traces.png` e lo screenshot del workflow. |
| **Ollama lento al primo colpo** (modello non in memoria) | il Task A impiega secondi invece di millisecondi | Warm-up obbligatorio prima di salire (checklist). Se succede comunque: "questo è il cold start, ve lo segnalo perché è un costo vero", e rilanciare. |
| **Ollama si blocca durante il talk** | timeout su tutte le rotte | `systemctl restart ollama` (o `ollama serve`) in un secondo terminale già aperto; nel frattempo replay. |
| **Stress test troppo lungo** | il batch completo dura 256 s {{stress.duration_s}} | Sul palco solo il replay `talk/replays/stress.json`; il run live, se proprio, è `./run.sh stress 10`. |
| **Advisor (Rizzo/Open-Jev) non risponde** | errore su `/v1/systemone` | Il secondo controllore dal vivo (4.8) è facoltativo: tabella del benchmark. Non stanno insieme in VRAM: avviarne solo uno. |
| **Proiettore/resa del deck 3D** | canvas lento o nero sul PC della sala | Usare il proprio portatile; in alternativa PDF di riserva. Testare la risoluzione del proiettore al soundcheck. |
| **Portatile che va in sospensione / batteria** | schermo nero | Alimentatore collegato, sospensione e screensaver disattivati, notifiche spente. |

---

# Checklist pre-palco

**T − 60 minuti (in camerino)**
- [ ] Alimentatore collegato; sospensione, screensaver e notifiche disattivati; Wi-Fi spento se non serve.
- [ ] `cd switchable-ai-public` (la cartella del clone)
- [ ] `./run.sh up` — gateway `:4000`, Langfuse `:3011`, Grafana `:3012`, n8n `:5678`; attendere che i container siano healthy (`docker compose -f infra/docker-compose.yml ps`).
- [ ] `./run.sh serve` in un terminale dedicato (API su `:8088`).
- [ ] `./run.sh rag-build` — indice della stiva aggiornato.
- [ ] Warm-up di Ollama (modello chat ed embedding in memoria, tenuti caldi):
  ```bash
  curl -s http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b","prompt":"ok","keep_alive":"2h"}' >/dev/null
  curl -s http://localhost:11434/api/embed    -d '{"model":"nomic-embed-text","input":"ok","keep_alive":"2h"}' >/dev/null
  ```
- [ ] `./run.sh demo-dry` (solo decisioni, nessun modello) e poi `./run.sh demo` una volta: deve uscire il fallback sul Task B.
- [ ] `./run.sh rag "Perché il router di base non usa un LLM per decidere?"` → deve citare l'ADR-001.
- [ ] `.env`: `OPENAI_API_KEY` **vuota** (il fallback del Task B è parte del racconto) — «[TODO speaker: decidere se per la demo dal vivo vuoi invece un cloud vero; in quel caso cambia la frase "oggi il jet non ha carburante"]».
- [ ] Se si mostra l'advisor: avviare **solo** Rizzo Flow (porta 8017) oppure Open-Jev (porta 8791), non entrambi.
- [ ] `./run.sh test` verde (non il mutation testing: è lento).
- [ ] Demo **senza** chiave cloud: il fallback reale del Task B fa parte del racconto e non dipende dalla rete della sala.

**T − 15 minuti (al tavolo)**
- [ ] Grafana aperto sulla dashboard Cockpit, finestra "Last 30 minutes", refresh 5s; Langfuse aperto sulle Traces.
- [ ] Terminale con font grande (almeno 20 pt), tema scuro, prompt corto; un secondo terminale pronto per riavviare Ollama.
- [ ] Deck aperto (`./run.sh deck`), replay dello stress test caricato, PDF di riserva aperto in una scheda.
- [ ] Ultimo warm-up di Ollama (gli stessi due `curl`).
- [ ] Bottiglietta d'acqua. Cronometro visibile: checkpoint a 07:45 (inizio demo), 17:30 (inizio turbolenza), 22:30 (flywheel).
