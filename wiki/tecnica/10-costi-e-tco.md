# Costi e TCO (`core/domain/pricing.py`)

## Prezzario

EUR per **1.000 token**, prezzo "blended" (stesso prezzo per input e output), mantenuto uguale al legacy per confrontabilità.

| Modello | €/1k token | €/Mtok |
|---|---:|---:|
| `local` (default per `ollama/…`, `vllm/…`) | 0,0002 | 0,20 |
| `ollama/qwen2.5:7b` | 0,0002 | 0,20 |
| `vllm/qwen2.5-1.5b` | 0,0001 | 0,10 |
| `cloud/gpt-4o` (**riferimento cloud**) | 0,0046 | 4,60 |
| `cloud/gpt-4o-mini` | 0,0004 | 0,40 |
| `cloud/deepseek` | 0,002 | 2,00 |

Il prezzo locale è una **stima energetica**. Un modello non in tabella prende il prezzo `local` se ha prefisso locale, altrimenti quello del riferimento cloud (scelta conservativa).

## Funzioni

```python
cost_of(model, tokens_in, tokens_out) = (tokens_in + tokens_out) / 1000 * price_per_1k(model)
cost_if_cloud(tokens_in, tokens_out)  = cost_of("cloud/gpt-4o", tokens_in, tokens_out)
```

I token sono quelli **contati dal motore** (`LLMResult`), mai stimati. Ogni `CallRecord` porta entrambi i costi, quindi il risparmio è calcolabile su qualsiasi sottoinsieme del registro.

## Attenzione: il risparmio "solo energia" è un rapporto di prezzi

Se tutto gira in locale, `1 − 0,0002/0,0046 = 95,65%`, **qualunque** cosa faccia il sistema. Il −96% della demo misura questo. Per un numero onesto servono rotte miste (stress test: −82%) e il TCO ammortizzato.

## Costo locale ammortizzato

```python
LocalTcoInputs(hw_eur, amort_months, watts, eur_kwh, tokens_per_sec, utilization)
local_cost_per_mtok(x) -> {"energy", "hardware", "total"}   # € per milione di token
```

Formule:

```
secondi_per_Mtok = 1.000.000 / tokens_per_sec
energia          = watts/1000 · secondi_per_Mtok/3600 · eur_kwh
token_ammortati  = amort_months·30·24·3600 · tokens_per_sec · utilization
hardware         = hw_eur / token_ammortati · 1.000.000
totale           = energia + hardware
```

L'hardware si paga anche quando la GPU è ferma, ma è diviso solo per i token prodotti davvero: da qui la **penalità di sottoutilizzo**.

Ipotesi del talk (dichiarata): 2.000 € di hardware, 36 mesi, 140 W, 0,30 €/kWh, throughput misurato ~42 tok/s (`qwen2.5:7b`, RTX 4070 Laptop).

| Utilizzo GPU | € / Mtok locale | Cloud (gpt-4o) |
|---:|---:|---:|
| 5% | 10,41 | 4,60 |
| 12% (pareggio) | ≈ 4,5 | 4,60 |
| 25% | 2,30 | 4,60 |
| 80% | 0,91 | 4,60 |

Sotto circa il **12%** di utilizzo il locale costa più del cloud.

Validazioni: `utilization` in (0, 1], `tokens_per_sec > 0`, altrimenti `ValueError`.

## Dove si vede

- `./run.sh report`, `GET /v1/report`, tool MCP `cost_report`: € reali, € se tutto-cloud, risparmio;
- Grafana: "€ reali", "€ se tutto-cloud", "Risparmio", "Costo cumulato";
- `benchmarks/results/tco.json`: demo misurata + `local_amortized_eur_per_mtok` + throughput.

## Aggiungere un modello al prezzario

1. Aggiungi la voce in `PRICING`.
2. Aggiungi o aggiorna un test in `tests/test_domain_pricing.py`.
3. Se cambia il riferimento cloud (`CLOUD_REFERENCE`), tutti i "€ se tutto-cloud" storici restano calcolati col vecchio: rigenera i benchmark.

## Test

`tests/test_domain_pricing.py`. Mutazioni: conteggio token rotto, "tutto costa zero".
