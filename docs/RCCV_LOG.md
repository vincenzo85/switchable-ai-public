# RCCV Log — un blocco per ciclo

Formato: **R**ichiesta (cosa) / **C**ontesto (perché, stato) / **V**incoli (regole) / **V**erifica (evidenza).
Continua il registro di `router_llm_legacy/docs/RCCV_LOG.md` (WP1–WP6, luglio 2026).

---

## B0 — Bootstrap esagonale (2026-10-03)
- **Richiesta**: nuovo repo con `init-repo switchable_ai`.
- **Contesto**: il legacy funzionava ma non era esagonale; il talk promette più cose di quante ne facesse.
- **Vincoli**: `core/` solo stdlib; test prima del codice.
- **Verifica**: test del template verdi. Trovato e corretto un bug della guardia di confine: confrontava per prefisso, quindi `requests` passava perché inizia con `re` (test di regressione aggiunto).

## B1 — Porting di policy, prezzi, RAG, MCP (2026-10-03)
- **Richiesta**: riscrivere i moduli legacy contro le porte; i test WP1–WP4 diventano contratti.
- **Contesto**: nel legacy il Task C stampava i chunk RAG ma non li passava al modello.
- **Vincoli**: regole dure prima della complessità; la compressione solo sulla rotta a pagamento.
- **Verifica**: suite verde; mutation 13/13 (poi 14/14). Il difetto RAG del legacy è coperto da un test e da una mutazione.

## C1–C5 — Infrastruttura e n8n (2026-10-03)
- **Richiesta**: compose con LiteLLM, Langfuse, Prometheus, Grafana, n8n; workflow di intake.
- **Contesto**: il firewall della macchina scarta il traffico rete-Docker → host.
- **Vincoli**: porte libere (3011, 3012, 9091, 4000, 5678, 8088); nessun servizio esposto oltre 127.0.0.1.
- **Verifica**: tutti i container healthy. Il gateway fa fallback `smart-cloud → fast-local` e il core lo rileva dal campo `model`. Il primo run reale di n8n ha trovato due bug del router: l'intento veniva letto dal corpo del documento, e un'estrazione di 600 caratteri finiva in cloud. Corretti con test di regressione.

## C6 — RAG SDLC (2026-10-03)
- **Richiesta**: knowledge base vera e domande di riferimento con la fonte attesa.
- **Verifica**: hit@3 dall'83% al 100% con due correzioni misurate: chunk per sezione markdown e prefissi di task di `nomic-embed-text`.

## C7–C8 — Compressione e vLLM (2026-10-03)
- **Verifica**: compressione guidata dalla domanda −68% di token senza perdite; alla cieca stessi token, accuratezza al 70%. vLLM 6,7× il throughput di Ollama a concorrenza 16; Ollama più veloce a richiesta singola. vLLM gira sulla porta 8010, perché la 8000 è occupata.

## C9–C10 — Stress test e Data Flywheel (2026-10-03)
- **Vincoli**: senza chiave cloud, il cloud è **simulato e dichiarato** (modello locale, listino cloud, turbolenza programmata).
- **Verifica**: 100/100 completati, 4 fallback, budget guard attivo, 0 violazioni di residency; flywheel con 49 esempi anonimizzati.

## A1 — Router appreso, su richiesta dell'utente (2026-10-03)
- **Richiesta**: usare Rizzo Flow e Open-Jev come router attivabile, con test.
- **Vincoli**: le regole dure decidono cosa è ammesso; il modello sceglie solo tra le rotte ammesse; modalità off / shadow / active.
- **Verifica**: sul set di controllo (32 parafrasi) le regole fanno 53%, Rizzo 66% (+76 ms), Open-Jev 66% (+204 ms). Il 100% delle regole sul batch "di casa" è autoreferenziale ed è dichiarato come tale.

## D — Bibliografia (2026-10-03)
- **Verifica**: 26/26 paper verificati sul DB di `best_paper` (sola lettura). I numeri citabili sono controllati contro gli abstract; due titoli abbreviati sono stati rivisti a mano.

## E–F — Canovaccio e deck (2026-10-03)
- **Richiesta**: canovaccio con un esperto di presentazioni (subagent speaker coach); deck 3D in stile "In principio era il Verbo".
- **Vincoli**: numeri solo da `talk/numbers.json`; offline-first.
- **Verifica**:
  - test Playwright: nessun errore, nessuna richiesta di rete, nessun numero senza fonte, tempi del canovaccio = 30:00;
  - demo dal vivo provata contro l'API reale;
  - PDF di riserva.

## A2 — Messa a punto del secondo controllore (2026-10-04)
- **Richiesta**: router più accurato.
- **Contesto**: `rizzo calibrate` adatta solo le temperature, quindi non cambia la scelta; tutti gli errori delle regole cadono nei casi senza parole chiave.
- **Vincoli**: il set di controllo diventa TEST e non si tocca; per la messa a punto c'è un set DEV nuovo (42 richieste); le regole dure non cambiano. Un difetto delle regole ("sceglieresti" che scatta come `scegli`) è stato notato e lasciato com'è, perché correggerlo dopo averlo visto nel test significherebbe tarare sul test.
- **Verifica**: griglia di 8 configurazioni sul dev → descrizioni v2, ordine singolo, active. Sul test: Rizzo 78% (prima 66%), Open-Jev 56%. Doppio ordine senza guadagno. Nuova modalità `fallback` e `keyword_hit` nel dominio, con test e una mutazione in più (15/15).

## F2 — Il talk come viaggio (2026-10-04)
- **Richiesta**: struttura a fasi di volo (decollo, crociera, atterraggio) visibile anche graficamente. Sezioni: di cosa parliamo, per chi (stakeholder), come lo diciamo, tecnologie e perché, cosa dice la ricerca, cosa abbiamo trovato, come funziona, perché l'ho creato, limiti. Evento: MLOps, 29 ottobre 2026.
- **Vincoli**: 30:00 con Q&A; numeri solo da `numbers.json`, compresi quelli della letteratura (`lit.*`, verificati negli abstract).
- **Verifica**:
  - canovaccio a 30 beat in 7 fasi più gli arrivi;
  - deck a 32 step con indicatore di volo (profilo di altitudine scalato sul tempo, fase corrente, aereo che avanza), testato in Chrome;
  - QR del repository;
  - PDF di riserva a 32 pagine;
  - suite completa verde.

## F3 — V2 "AI Traffic Control" (2026-10-04)
- **Richiesta**: review esterna del deck. Meno catalogo, più storia: circa 21–23 passaggi principali, il 96% come open loop risolto dal TCO, 3D semantico, quattro soli WOW. Titolo "Non serve sempre un modello migliore. Serve una torre di controllo.", con il titolo ufficiale come sottotitolo.
- **Vincoli** (decisi dallo speaker):
  - per chi, tecnologie e ricerca sintetizzati nel racconto e completi in appendice;
  - limiti e metodo restano nella storia;
  - AI Traffic Control è il nome del concept visivo.
- **Verifica**:
  - canovaccio a 23 beat (30:00 con Q&A) e appendice A.1–A.6;
  - motore con rotte a stato: aperta/chiusa con motivo, svelamento progressivo, pacchetti respinti e timeout che tornano;
  - test Playwright per la chiusura della pista (residency e budget), le quattro richieste del routing, l'appendice col tasto A;
  - filmini dei WOW in `talk/screens/wow-*.png`;
  - suite completa verde.

## F4 — V3 "una slide, una idea" (2026-10-04)
- **Richiesta**: più visiva, icone dove possibile, più slide e meno testo. Le immagini si genereranno dopo: per ora serve il piano slide per slide, con l'alternativa in SVG o 3D.
- **Verifica**:
  - 35 slide nel racconto (era 24) e 6 in appendice; testo ridotto a una frase o un numero per slide;
  - icone Lucide (ISC) incorporate offline;
  - campo `img` per slide, con `talk/IMMAGINI.md` generato al build (27 immagini da generare, prompt pronti);
  - fondali usati automaticamente se presenti in `talk/assets/img/`;
  - tempi divisi fra le slide che condividono un beat;
  - suite completa verde.

## 2026-10-04 — Deck red team separato
- **R**: critica red-team (10 attacchi alla tesi) → deck separato `talk/deck/src/slides_redteam.js`, 28 step, 30 min.
- **C**: ogni attacco ha risposta ❌→✅ con evidenza; numeri solo da `numbers.json` (6 nuove chiavi `lit.*` verificate negli abstract).
- **C**: 3D attenuato e senza piste nelle slide attacco/risposta (prima copriva citazioni e flussi); etichette di fase corte nascoste se non correnti.
- **V**: `tests/test_deck_redteam.py` 4/4, screenshot `talk/screens-redteam/`, PDF 28 pagine. `./run.sh deck-redteam`.
