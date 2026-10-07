# Indice wiki

Tre wiki per tre lettori diversi, più le pagine di classi e lezioni del progetto.

| Wiki | Per chi | Si parte da |
|---|---|---|
| **Per negati** | chi parte da zero e vuole far funzionare le cose | [per-negati/00-inizia-qui.md](per-negati/00-inizia-qui.md) |
| **Tecnica** | chi sviluppa, integra o gestisce il sistema | [tecnica/00-panoramica.md](tecnica/00-panoramica.md) |
| **Didattica** | chi vuole capire i concetti, con esempi ed esercizi | [didattica/00-percorso.md](didattica/00-percorso.md) |

## Wiki per negati (`per-negati/`)
- [Inizia qui](per-negati/00-inizia-qui.md) — cos'è, in una pagina
- [Installazione passo passo](per-negati/01-installazione.md)
- [Primi passi](per-negati/02-primi-passi.md) — cinque comandi e come leggerli
- [Ricette "voglio fare X → fai così"](per-negati/03-ricette.md)
- [Lo stack completo](per-negati/04-stack-completo.md) — Docker, Grafana, Langfuse, n8n
- [Problemi comuni](per-negati/05-problemi-comuni.md)
- [Glossario](per-negati/06-glossario.md)

## Wiki tecnica (`tecnica/`)
- [Panoramica](tecnica/00-panoramica.md) · [Routing policy](tecnica/01-routing-policy.md) · [Esecuzione](tecnica/02-esecuzione.md) · [Configurazione](tecnica/03-configurazione.md)
- [API HTTP](tecnica/04-api-http.md) · [CLI e MCP](tecnica/05-cli-e-mcp.md) · [RAG](tecnica/06-rag.md) · [Osservabilità](tecnica/07-osservabilita.md)
- [Infrastruttura](tecnica/08-infrastruttura.md) · [Advisor](tecnica/09-advisor.md) · [Costi e TCO](tecnica/10-costi-e-tco.md) · [Benchmark e numeri](tecnica/11-benchmark-e-numeri.md)
- [Test e qualità](tecnica/12-test-e-qualita.md) · [Estendere il sistema](tecnica/13-estendere.md)

## Wiki didattica (`didattica/`)
- [Il percorso](didattica/00-percorso.md)
- [01 Perché un router](didattica/01-perche-un-router.md) · [02 Architettura esagonale](didattica/02-architettura-esagonale.md) · [03 Routing deterministico](didattica/03-routing-deterministico.md)
- [04 Fallback e resilienza](didattica/04-fallback-e-resilienza.md) · [05 RAG locale](didattica/05-rag-locale.md) · [06 Costi veri e TCO](didattica/06-costi-veri-e-tco.md)
- [07 Compressione](didattica/07-compressione.md) · [08 Osservabilità](didattica/08-osservabilita.md) · [09 Router appreso](didattica/09-router-appreso.md)
- [10 Data Flywheel](didattica/10-data-flywheel.md) · [11 Metodo](didattica/11-metodo.md) · [12 Esercizi e soluzioni](didattica/12-esercizi-e-soluzioni.md)

## Classi (`classes/`)
- [ExecuteRequest](classes/ExecuteRequest.md) — il volo di una richiesta: decisione, fallback, escalation, costi
- [Policy](classes/Policy.md) — `classify`, `decide_route`, `reroute`: la torre di controllo deterministica
- [AdvisedRouter](classes/AdvisedRouter.md) — Rizzo Flow / Open-Jev come secondo controllore
- [Porte e adapter](classes/Porte-e-adapter.md) — chi implementa cosa e dove si sceglie

## Lezioni (`lessons/`)
- [Guardia di confine per prefisso](lessons/guardia-confine-prefisso.md)
- [L'intento sta nell'istruzione, non nel documento](lessons/intento-nell-istruzione.md)
- [Il firewall scarta Docker → host](lessons/docker-firewall-host-network.md)
- [Prefissi di task e chunk per sezione](lessons/rag-prefissi-e-sezioni.md)
- [Il risparmio che esce sempre uguale](lessons/risparmio-tautologico.md)
- [Il 100% che si dà ragione da solo](lessons/set-di-controllo.md)
- [Numeri del talk: una sola fonte, verificata dai test](lessons/numeri-una-fonte.md)
- [Le parole delle rotte contano più dei trucchi](lessons/descrizioni-contano-dev-test.md)
