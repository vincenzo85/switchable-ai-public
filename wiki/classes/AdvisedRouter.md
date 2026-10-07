# AdvisedRouter (`core/use_cases/advisor.py`)

Un modello piccolo che sceglie tra candidati con probabilità (contratto `/v1/systemone`: Rizzo Flow su :8017, Open-Jev su :8791; adapter `adapters/llm/systemone.py`).

- `off`: non viene chiamato.
- `shadow` (default): viene chiamato e misurato (`advisor_*` nel `CallRecord` e in Prometheus), ma decide la regola.
- `fallback`: il modello viene chiamato solo se `classification.keyword_hit` è falso, cioè quando la regola sta tirando a indovinare.
- `active`: decide il modello, solo tra le rotte ammesse (il cloud non viene nemmeno offerto se le regole lo vietano) e solo sopra `min_confidence`.

`both_orders=True` chiede due volte con i candidati in ordine inverso e media le probabilità: misurato, nessun guadagno. Le descrizioni delle rotte sono configurabili; il default (v2) è stato scelto sul dev.

Errori del server → `Advice.error`, vince la regola. La latenza dell'advisor è sommata a quella della richiesta.

Attivazione: `SAI_ADVISOR=rizzo|openjev`, `SAI_ADVISOR_MODE`, `SAI_ADVISOR_MIN_P`. I due server non stanno insieme in 8 GB di VRAM.
