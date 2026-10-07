# ADR-003 — Advisor di rotta (Rizzo Flow, Open-Jev) prima in shadow

Stato: accettata.

Contesto: sulla macchina girano due modelli piccoli che espongono `/v1/systemone` e restituiscono probabilità su una scelta: Rizzo Flow (Spark-X2.5-4B Q8_0, porta 8017) e Open-Jev-2B (porta 8791). Non stanno insieme negli 8 GB di VRAM: se ne avvia uno alla volta.

Decisione: l'advisor si attiva con `SAI_ADVISOR=rizzo|openjev`. La modalità di default è `shadow`: decide la regola, l'advisor viene interrogato e misurato (accordo, confidenza, latenza). In `active` l'advisor sceglie solo tra le rotte ammesse dalle regole dure e sotto `SAI_ADVISOR_MIN_P` vince la regola.

Conseguenze: la latenza dell'advisor viene sommata a quella della richiesta, così il costo dello switch è visibile. Si passa ad `active` solo se il benchmark (`./run.sh bench advisor`) mostra che l'advisor migliora l'accuratezza di rotta abbastanza da giustificare la latenza.

## Aggiornamento 2026-10-04 — messa a punto misurata

Protocollo: configurazioni provate solo su un set **dev** separato (`benchmarks/routing_dev.py`, 42 richieste); la migliore è stata misurata **una volta** sul set di controllo (`routing_heldout.py`, 32 richieste). Risultati in `benchmarks/results/router_tuning.json`.

- **Descrizioni delle rotte riscritte** (v2, ora default in `core/domain/policy.py`). Rizzo Flow passa dal 66% al **78%** sul test, con circa 90 ms di latenza media e 1 richiesta su 32 mandata in cloud senza motivo. Le regole restano al 53%.
- **Doppio ordine dei candidati:** nessun guadagno, latenza doppia. Resta disponibile ma spento.
- **Modalità `fallback`** (il modello viene chiamato solo quando nessuna parola chiave ha deciso il tipo): sul dev è leggermente sotto `active` (83% contro 86%), perché il dev è scritto apposta senza parole chiave. Su traffico reale salta la maggior parte delle chiamate.
- **Open-Jev con le stesse descrizioni** scende al 56% e manda 6 richieste in cloud senza motivo: le descrizioni sono state scelte con Rizzo e non si trasferiscono.

Raccomandazione: `SAI_ADVISOR=rizzo`, `SAI_ADVISOR_MODE=fallback` in produzione; `shadow` per misurare su traffico nuovo. Open-Jev non va usato in modalità attiva senza una messa a punto sua.
