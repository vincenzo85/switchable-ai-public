# Numeri del talk: una sola fonte, verificata dai test

`benchmarks/results/*.json` → `benchmarks/build_numbers.py` → `talk/numbers.json`, con valore, display, fonte e data. Deck e canovaccio citano le chiavi `{{...}}`:

- `tests/test_deck.py`: ogni chiave si risolve; nessuna cifra con unità di misura scritta a mano nelle slide (i parametri degli esperimenti sono marcati `data-param`); i numeri mostrati coincidono con `numbers.json`.
- `tests/test_talk_numbers.py`: nel canovaccio la cifra scritta accanto a `{{chiave}}` deve essere quella attuale. Se un benchmark viene rifatto, il testo vecchio diventa rosso.

Il revisore ha comunque trovato "Sedici richieste" scritto in lettere e gli screenshot di Grafana con numeri di un altro run: i test non vedono tutto, la revisione umana (o di un agente) serve ancora.
