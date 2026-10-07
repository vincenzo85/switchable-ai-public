# Roadmap

## 00 — Bootstrap ✅
Scheletro esagonale da `hexainit`, test di confine, commit iniziale.

## 01 — Porting del legacy ✅
Policy, prezzi, registro costi, RAG e MCP di `router_llm_legacy` riscritti contro le porte. I test WP1–WP4 sono diventati contratti. Il mutation testing è passato da 5 a 15 sabotaggi.

## 02 — Le promesse dell'abstract ✅
- Docker con LiteLLM, Langfuse, Prometheus, Grafana e n8n.
- vLLM sull'host.
- Data residency, budget guard, escalation, compressione sulla sola rotta a pagamento.
- RAG con citazione delle fonti.
- Data Flywheel, stress test di atterraggio, advisor Rizzo Flow / Open-Jev.

## 03 — Il talk ✅
Benchmark reali, `talk/numbers.json`, bibliografia verificata, canovaccio, risposte al presentatore (non incluse nella versione pubblica), deck 3D con vista relatore, PDF di riserva.

## 04 — Prossimi passi (non fatti)
- **Router:** ✅ (2026-10-04) Rizzo Flow con descrizioni v2 passa al 78% sul test (regole: 53%). Prossimo passo: calibrare le temperature con l'API nativa, per usare `min_confidence` come soglia di astensione; mettere a punto Open-Jev per conto suo.
- **Validatori per l'escalation:** oggi l'escalation scatta solo su risposta vuota o su un validatore passato a mano.
- **Fine-tuning reale dal flywheel:** oggi il dataset esiste, l'addestramento no.
- **Cloud vero nello stress test:** quando una chiave è disponibile, ripetere `benchmarks/run_stress.py` senza simulazione.
- **LLMLingua-2** come secondo compressore, confrontato con quello estrattivo.
