# 09 — Router appreso (l'advisor)

## Obiettivi

- Combinare un router a regole con un piccolo modello **senza** cedere le regole dure.
- Usare la modalità **shadow** per misurare prima di fidarsi.
- Fare una messa a punto onesta con set **dev** e **test** separati.

## Il concetto

Le regole sbagliano sulle richieste formulate in modo inatteso ([lezione 03](03-routing-deterministico.md): 53% sul set di controllo). Un piccolo modello che "capisce" il testo può fare meglio, ma:
- costa latenza a ogni richiesta;
- può sbagliare in modi imprevedibili;
- può essere manipolato.

Soluzione a strati:

```
regole dure  →  decidono COSA è ammesso (il cloud c'è o non c'è tra le opzioni)
advisor      →  sceglie TRA le rotte ammesse, con una probabilità
soglia       →  sotto una confidenza minima, vince la regola
```

E un'adozione graduale:

| Modalità | Cosa succede | A cosa serve |
|---|---|---|
| `off` | l'advisor non esiste | — |
| `shadow` | l'advisor viene chiamato e registrato, ma decide la regola | **misurare** accordo, confidenza e latenza su traffico vero, senza rischi |
| `fallback` | l'advisor viene chiamato solo quando la regola tira a indovinare (`keyword_hit` falso) | pagare la latenza solo dove le regole sbagliano |
| `active` | l'advisor decide sempre (sopra la soglia) | quando le misure lo giustificano |

## Come è fatto qui

- `core/use_cases/advisor.py`: `AdvisedRouter`, `Advice`.
- `core/ports`: `RouteAdvisorPort.choose(state, question, candidates) → (probabilità, latenza)`.
- `adapters/llm/systemone.py`: il client per due modelli locali (Rizzo Flow, Open-Jev) che espongono un'API `/v1/systemone` con domande a scelta multipla.

Garanzie verificate da test e mutation testing:
- il cloud **non viene nemmeno offerto** come candidato se le regole lo vietano;
- se l'advisor è giù o risponde con id non offerti, vince la regola;
- la latenza dell'advisor è sommata a quella della richiesta (il costo dello switch è visibile).

## Esempio svolto — un advisor che vuole sempre il cloud

Un advisor "fazioso" mostra bene che cosa le regole proteggono:

```python
from core.ports import RouteAdvisorPort
from core.use_cases.advisor import AdvisedRouter
from core.domain.policy import decide_route

class AlwaysCloud(RouteAdvisorPort):
    name = "sempre-cloud"
    def choose(self, state, question, candidates):
        ids = [c for c, _ in candidates]
        if "cloud" in ids:
            return {c: (0.9 if c == "cloud" else 0.1 / (len(ids) - 1)) for c in ids}, 42
        return {c: 1 / len(ids) for c in ids}, 42

for mode in ("shadow", "active"):
    ar = AdvisedRouter(AlwaysCloud(), mode=mode)
    for p in ("Classifica questo ticket: login rotto", "Documento riservato: classifica questo ticket"):
        d, a = ar.decide(p, decide_route(p))
        print(mode, d.route, a.choice, round(a.p, 2), a.applied, list(d.rules))
```

Output:

```
shadow local cloud 0.9 False []
shadow local local 0.5 False ['data_residency']
active cloud cloud 0.9 True ['advisor']
active local local 0.5 False ['data_residency']
```

- In **shadow** l'advisor vota cloud ma la rotta resta locale: si registra solo il disaccordo.
- In **active** sul ticket normale l'advisor vince (`applied=True`, regola `advisor`).
- Sul documento riservato, in entrambe le modalità, il cloud **non era tra le opzioni**: l'advisor ha potuto scegliere solo tra `local` e `local_rag`.

## La messa a punto, fatta onestamente

Dati del progetto (`benchmarks/results/advisor.json`, `router_tuning.json`):

| Router | Set di controllo (32) | Latenza |
|---|---:|---:|
| regole | 53% | 0 ms |
| Rizzo Flow, prima versione | 66% | 76 ms |
| Open-Jev, prima versione | 66% | 204 ms |
| **Rizzo Flow, descrizioni v2** | **78%** | ~90 ms |
| Open-Jev, descrizioni v2 | 56% | — |

Il protocollo:
1. Il set di controllo era **già stato visto** (si sapeva dove sbagliavano le regole). Usarlo per scegliere le impostazioni l'avrebbe trasformato in un set di casa.
2. Si è creato un set **dev** nuovo (42 richieste) e si sono provate 8 configurazioni **solo lì**: modalità (active, fallback) × doppio ordine dei candidati (no, sì) × descrizioni delle rotte (v1, v2).
3. La migliore è stata misurata **una volta** sul set di controllo, che a quel punto fa da **test**.

Cosa ha funzionato: solo le **descrizioni delle rotte**. La frase decisiva: "usa il cloud quando serve ragionare, *anche se la domanda è breve*". Il doppio ordine (contro il bias di posizione): nessun guadagno, latenza doppia.

E una sorpresa: le stesse descrizioni **peggiorano** Open-Jev (66% → 56%, 6 richieste mandate in cloud senza motivo). Un prompt non si trasferisce gratis da un modello all'altro.

Raccomandazione finale (ADR-003): Rizzo Flow in modalità `fallback` in produzione, `shadow` per misurare su traffico nuovo.

## Esercizi

1. ★ Nell'esempio, metti `min_confidence=0.95` in modalità active. Cosa cambia per il ticket normale? Cosa dice `Advice.note`?
2. ★ Riscrivi `AlwaysCloud` perché sollevi `ProviderError`. Cosa restituisce `decide`?
3. ★★ Con `mode="fallback"`, l'advisor viene chiamato per "Classifica questo ticket: login rotto"? E per "Quale database conviene per i nostri eventi, Postgres o Kafka?"? Verifica guardando se `Advice` è `None`.
4. ★★ Spiega perché misurare 8 configurazioni sul set di controllo e poi riportare la migliore sarebbe un risultato gonfiato, anche senza toccare nessuna regola.
5. ★★★ Progetta un esperimento in shadow per decidere se passare in `active` in produzione: quali campi del `CallRecord` useresti, per quanto tempo, con quale soglia di decisione?

## Da ricordare

- Il modello consiglia tra le rotte **ammesse**; le regole dure restano deterministiche.
- Prima shadow (misura), poi fallback o active (fiducia), mai al contrario.
- Dev per scegliere, test per misurare una volta. Un set già visto non è più un test.
