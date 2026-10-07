# TCO Report — misurato, non stimato

Macchina: workstation locale, Ollama nativo. Run per task: 3. Chiave cloud presente: NO → fallback locale reale.

| Task | Rotta decisa | Modello eseguito | Fallback? | Latenza | Token in/out | € reale | € se tutto-cloud |
|---|---|---|---|---:|---|---:|---:|
| A_classificazione | local | ollama/qwen2.5:7b | no | 4157ms | 84/3 | 0.000017 | 0.000400 |
| B_reasoning | cloud | ollama/qwen2.5:7b | SÌ | 21790ms | 378/1097 | 0.000295 | 0.006785 |
| C_rag_query | local_rag | ollama/qwen2.5:7b | no | 17091ms | 27/865 | 0.000178 | 0.004103 |

**Totale batch (3× i 3 task): €0.00121 reali vs €0.02774 se tutto andasse al cloud → risparmio 95.7%** (sui task instradati in locale; il cloud resta per ciò che lo merita).

## Aggregato dal costmeter (tutte le run)

| Model | Calls | Total Cost (EUR) | Avg Latency (ms) |
|---|---:|---:|---:|
| ollama/qwen2.5:7b | 9 | 0.001206 | 12672.1ms |

*Prezzi: locale = stima energetica conservativa; cloud = listino pubblico. Tabella completa in `costmeter/meter.py` (PRICING, 6 voci).*
