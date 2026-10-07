# AGENTS.md

Regole per chi (umano o agente) lavora su questo repository.

## Architettura

* `core/` può importare solo la standard library di Python e altri moduli
  interni di `core/`. Mai `adapters/`, mai pacchetti esterni
  infrastrutturali (DB, HTTP, filesystem reale, ecc.).
* Le eccezioni sollevate da un adapter vanno catturate nell'adapter stesso
  e rimappate su eccezioni di dominio (`core/domain/errors.py`).
* Ogni caso d'uso riceve le sue porte per costruttore; solo `app/main.py`
  (la composition root) decide quale adapter concreto passare.

## Qualità

* Test-first: nessuna feature senza un test che ne definisce il
  comportamento e fallisce preliminarmente per il motivo atteso.
* `make check` deve essere verde prima di ogni commit.
* Ogni classe/porta/adapter significativo ha una pagina gemella in
  `wiki/classes/`. Ogni step di lavoro concluso ha una voce in
  `wiki/lessons/` se ha insegnato qualcosa di non ovvio.

## Commit

* Preferisci due commit per step: uno con codice+test verdi
  (`feat(scope): ...` / `test(scope): ...`), uno con la documentazione
  (`docs(scope): ...`).
