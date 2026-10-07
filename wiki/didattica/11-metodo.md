# 11 — Metodo: dimostrare che funziona

## Obiettivi

- Applicare il **test-first** a un sistema con componenti esterni.
- Usare il **mutation testing** per scoprire test ciechi.
- Evitare i numeri che "si danno ragione da soli": set di controllo, dev/test, simulazioni dichiarate, numeri con fonte.

## Il concetto

Un sistema AI è facile da presentare bene e difficile da dimostrare. Questo progetto si è dato quattro regole.

### 1. Test-first, con adapter finti ma realistici

Nessuna feature senza un test che la definisce e fallisce **prima**, per il motivo atteso. Per testare fallback, timeout e costi senza modelli veri servono adapter in memoria che si comportano come quelli veri: `FakeLLM` solleva `ProviderTimeout` se la latenza supera il timeout, esattamente come il client HTTP.

E una regola contro le "feature fantasma" (`DEFINITION_OF_DONE.md`): una feature non è finita se esiste nei file ma non viene mai chiamata a runtime. Ogni feature ha un test che fallisce se la si **scollega** dalla composition root (`tests/test_wiring.py`).

### 2. Mutation testing: chi controlla i test?

Una suite verde non dice che i test controllano qualcosa. Il mutation testing **rompe apposta** il codice nei punti critici e pretende che almeno un test diventi rosso. Una mutazione che sopravvive = un test cieco.

Qui le mutazioni sono scelte sui punti che reggono la tesi (`tools/mutation_check.py`, 15 su 15 uccise):
- "data residency spenta: il dato sensibile va in cloud";
- "il fallback non viene mai eseguito";
- "tutto costa zero: il TCO è una favola";
- "il flywheel esporta dati personali in chiaro"; …

### 3. Set di controllo e dev/test

- Il batch dello stress test e le regole del router li ha scritti la stessa persona, con le stesse parole: 100% di rotte giuste. **Autoreferenziale.**
- Un set di 32 richieste scritte apposta senza quelle parole: 53%. **Questo** è il numero da dichiarare.
- Per migliorare il router serve un terzo set (**dev**): si prova lì, si misura una volta sul **test**.

Anche un "100%" di Rizzo Flow al primo giro era falso: 52 errori su 100 erano finiti sulla regola di riserva. Si è scoperto guardando **il numero degli errori**, non l'accuratezza.

### 4. Numeri con fonte, simulazioni dichiarate

- Ogni numero del talk viene da un file in `benchmarks/results/`, con data, commit e macchina, ed è aggregato in `talk/numbers.json`. Il deck e il canovaccio citano la chiave; i test falliscono se una cifra non ha fonte o è vecchia.
- Lo stress test usa un cloud **simulato**: è scritto nel codice, nei risultati, sulle slide e a voce.
- Le citazioni della letteratura usano solo numeri presenti negli **abstract** verificati.

## Come è fatto qui

| Regola | Dove |
|---|---|
| test-first, confini | `AGENTS.md`, `DEFINITION_OF_DONE.md`, `tests/test_architecture_boundaries.py` |
| adapter realistici | `adapters/memory/__init__.py`, `tests/conftest.py` (server HTTP finto) |
| mutation testing | `tools/mutation_check.py`, `benchmarks/results/mutation.json` |
| set di controllo, dev/test | `benchmarks/routing_heldout.py`, `benchmarks/routing_dev.py`, `run_router_tuning.py` |
| numeri con fonte | `benchmarks/build_numbers.py`, `tests/test_talk_numbers.py`, `tests/test_deck.py` |
| lezioni imparate | `wiki/lessons/` |

## Esempio svolto — una mutazione a mano

1. Apri `core/domain/policy.py` e trova:
   ```python
       if c.sensitive:
           rules.append("data_residency")
   ```
2. Cambia `if c.sensitive:` in `if False:` e salva.
3. Lancia:
   ```bash
   .venv/bin/python -m pytest -q -x
   ```
4. La suite diventa **rossa**: almeno un test (per esempio `test_sensitive_complex_task_never_goes_cloud`) se ne accorge. La mutazione è "uccisa".
5. **Ripristina** la riga (`git checkout core/domain/policy.py`).

Lo script `./run.sh mutation` fa la stessa cosa per 15 mutazioni e ripristina sempre il file, anche se si interrompe.

## Esercizi

1. ★ Lancia `./run.sh mutation` e leggi l'output: quante mutazioni, quante uccise, quanto tempo?
2. ★★ Inventa una mutazione nuova in `core/domain/pricing.py` (per esempio: un modello sconosciuto prende il prezzo locale invece di quello cloud). Applicala a mano: un test se ne accorge? Se no, scrivi il test che manca.
3. ★★ Scrivi 5 richieste da aggiungere a un **nuovo** set di controllo per il router, senza guardare le parole chiave delle regole. Poi misurale: quante ne indovina?
4. ★★ Trova nel progetto un numero che sarebbe stato facile presentare in modo ingannevole e spiega come è stato reso onesto (suggerimenti: −96%, 100% del router, stress test).
5. ★★★ Scegli una feature (per esempio la compressione) e verifica la regola del test di scollegamento: rompi il cablaggio in `app/composition.py` (es. non passare il compressore) e controlla quale test fallisce. Se nessuno fallisce, hai trovato una feature fantasma.

## Da ricordare

- Un test verde non basta: rompi il codice e guarda se i test se ne accorgono.
- Un numero misurato sui dati con cui hai costruito il sistema si dà ragione da solo: serve un set che non hai visto.
- Ogni numero ha una fonte, una data e una macchina; ogni simulazione è dichiarata.
