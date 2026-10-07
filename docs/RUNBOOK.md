# Runbook operativo

## Il cloud non risponde o è lento

Sintomo: nel pannello "Turbolenza" della dashboard Cockpit salgono i fallback; nel registro i `fallback_reason` riportano timeout o errori HTTP del provider.

Cosa succede da solo: ogni richiesta instradata in cloud viene ripetuta sul modello locale (`SAI_LOCAL_MODEL`). Il gateway LiteLLM ha lo stesso fallback (`smart-cloud → fast-local`). Gli utenti ricevono comunque una risposta, con qualità più bassa sui task complessi.

Cosa fare:
1. Controllare `./run.sh report`: se i fallback superano il 20% delle richieste cloud, abbassare `SAI_CLOUD_TIMEOUT_S` per non far aspettare gli utenti prima del fallback.
2. Se il disservizio dura più di un'ora, attivare `SAI_LOCAL_ONLY=true` e riavviare l'API: nessuna richiesta proverà il cloud.
3. Al rientro, riportare `SAI_LOCAL_ONLY=false` e controllare che i fallback tornino a zero.

## Budget cloud esaurito

Sintomo: il contatore "budget guard" nella dashboard sale; le richieste complesse restano in locale.

Cosa fare: è il comportamento voluto. Per alzare il budget modificare `SAI_BUDGET_EUR`; il residuo si azzera ogni giorno (UTC).

## Violazione di data residency

Il pannello "Violazioni residency" deve restare a 0. Se diventa maggiore di zero: fermare l'API, esportare `data/calls.jsonl`, cercare i record con `sensitive=true` e modello `cloud/…`, aprire un incidente. Il workflow n8n risponde con codice 500 e stato `residency_violation` in questo caso.

## L'indice RAG è vuoto o vecchio

Lanciare `./run.sh rag-build`. L'indice comprende `README.md`, `MISSION.md`, `docs/`, `wiki/`, `infra/`, i documenti ingeriti da n8n in `data/kb/` e la storia git.

## Procedura di rilascio

1. `./run.sh check` (test, confini esagonali, mutation testing) deve essere verde.
2. Aggiornare `infra/litellm.yaml` solo con un deploy canary (vedi ADR sul gateway).
3. Rigenerare i numeri del talk con `./run.sh numbers` se sono cambiati i benchmark.
