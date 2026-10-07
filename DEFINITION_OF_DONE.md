# Definition of Done

## Regole di qualità

* **Test-first obbligatorio**: nessuna feature senza un test che la
  definisce e fallisce preliminarmente per il motivo atteso.
* **Confini esagonali**: `core/` importa solo standard library e altri
  moduli di `core/`. Le eccezioni infrastrutturali vengono mappate su
  eccezioni di dominio dentro l'adapter che le solleva.
* **Wiki obbligatoria**: ogni classe/porta/adapter significativo ha una
  pagina in `wiki/classes/`; ogni step concluso una voce in
  `wiki/lessons/` se ha insegnato qualcosa di non ovvio.

## Policy anti-phantom-feature

Una feature è vietata e uno step non può dirsi completo se la feature:

1. esiste solo nei file ma non viene mai invocata a runtime;
2. ha test che controllano solo stringhe statiche invece del comportamento;
3. ha benchmark o verifiche finte (risultato atteso restituito senza
   eseguire la computazione reale);
4. è segnata come completa in una roadmap ma non è cablata nel runtime;
5. è documentata come reale ma non eseguita dal flusso applicativo.

### Regola del test di scollegamento

Ogni feature completa ha almeno un test che fallisce se viene scollegata
dal runtime (es. rompendo il cablaggio nella composition root e verificando
che il test a valle fallisca di conseguenza).
