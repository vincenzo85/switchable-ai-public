# 06 — Costi veri e TCO

## Obiettivi

- Calcolare il costo di una chiamata a partire dai token.
- Riconoscere un **risparmio tautologico** (un numero che non può non uscire).
- Calcolare il costo locale **ammortizzato** e il punto di pareggio con il cloud.

## Il concetto

### Costo per chiamata

I modelli si pagano a **token** (circa 4 caratteri). Il progetto usa un prezzo per 1.000 token uguale per input e output:

```
costo = (token_in + token_out) / 1000 × prezzo_per_1k(modello)
```

| Modello | €/1k token |
|---|---:|
| locale (Ollama, vLLM) | 0,0002 (stima: solo energia) |
| cloud di riferimento (`cloud/gpt-4o`) | 0,0046 |

Ogni richiesta registra **due** costi: quello reale e quello "se fosse andata tutta in cloud" (stessi token, prezzo cloud). Il risparmio è `1 − reale / se_cloud`.

### Il risparmio tautologico

Se tutto gira in locale:

```
risparmio = 1 − 0,0002 / 0,0046 = 95,65%
```

**Qualunque** richiesta, qualunque modello, qualunque qualità: esce sempre 95,65%. La demo del talk mostra "−96%" e poi lo smonta: è il rapporto tra due listini, non una misura del sistema.

Regola pratica: **diffida di ogni percentuale di risparmio che non cambia quando cambia il carico.**

Il numero onesto della demo con rotte miste (stress test: 70 locali, 15 cloud, 15 RAG, budget che si esaurisce) è **−82%**.

### Il TCO: l'hardware si paga anche da fermo

"Locale = solo elettricità" dimentica che la GPU va **comprata**. Il costo vero per milione di token (*TCO*, Total Cost of Ownership):

```
energia   = watt/1000 × (secondi per Mtok)/3600 × €/kWh
hardware  = costo_hw / (token prodotti in tutto il periodo di ammortamento)
token prodotti = mesi × 30 × 24 × 3600 × token/s × utilizzo
totale    = energia + hardware
```

La parola chiave è **utilizzo**: la frazione di tempo in cui la GPU lavora davvero. L'hardware costa uguale; se la GPU lavora poco, quel costo si divide su pochi token.

## Come è fatto qui

`core/domain/pricing.py`: `PRICING`, `cost_of`, `cost_if_cloud`, `LocalTcoInputs`, `local_cost_per_mtok`. Benchmark: `benchmarks/run_tco.py` (throughput misurato con Ollama).

Ipotesi dichiarata del talk: 2.000 € di hardware, 36 mesi, 140 W, 0,30 €/kWh, ~42 token/s misurati.

## Esempio svolto

```python
from core.domain.pricing import cost_of, cost_if_cloud, local_cost_per_mtok, LocalTcoInputs

# 1. il risparmio tautologico
print(1 - cost_of("ollama/qwen2.5:7b", 500, 500) / cost_if_cloud(500, 500))      # 0.9565…

# 2. costo locale ammortizzato a diversi utilizzi
for u in (0.05, 0.12, 0.25, 0.80):
    x = local_cost_per_mtok(LocalTcoInputs(hw_eur=2000, amort_months=36, watts=140,
                                           eur_kwh=0.30, tokens_per_sec=42, utilization=u))
    print(f"{u:>4.0%}  energia {x['energy']:.2f}  hardware {x['hardware']:.2f}  totale {x['total']:.2f} €/Mtok")
```

Output:

```
0.9565217391304348
  5%  energia 0.28  hardware 10.21  totale 10.48 €/Mtok
 12%  energia 0.28  hardware 4.25  totale 4.53 €/Mtok
 25%  energia 0.28  hardware 2.04  totale 2.32 €/Mtok
 80%  energia 0.28  hardware 0.64  totale 0.92 €/Mtok
```

Il cloud di riferimento costa **4,60 €/Mtok**. Quindi:
- al 5% di utilizzo il locale costa **più del doppio** del cloud;
- il pareggio è intorno al **12%**;
- all'80% il locale costa un quinto del cloud.

L'energia è sempre la stessa (0,28): a decidere è l'hardware diviso per l'utilizzo.

(I valori del talk, 10,41 / 2,30 / 0,91, usano il throughput misurato con più decimali.)

### Cosa cambia la conclusione

- **Più utilizzo** → il flywheel ([lezione 10](10-data-flywheel.md)) sposta lavoro dal cloud al locale e alza l'utilizzo: il TCO scende.
- **Più throughput** (modello più piccolo, vLLM con molte richieste in parallelo: 6,7× a concorrenza 16) → più token per lo stesso hardware.
- **Hardware già pagato** per altro → il costo marginale è quasi solo energia (ma è una scelta contabile: dichiarala).

## Esercizi

1. ★ Una richiesta usa 300 token in ingresso e 700 in uscita. Quanto costa in locale e quanto in cloud? Che risparmio esce? Cambia se i token diventano 3.000 e 7.000?
2. ★★ Trova il punto di pareggio con più precisione: scrivi una ricerca binaria su `utilization` tra 0,01 e 1 che si ferma quando il totale è 4,60.
3. ★★ Se il throughput raddoppia (84 token/s), quanto costa il locale al 5% di utilizzo? E dove si sposta il pareggio?
4. ★★ Nello stress test il risparmio è −82% e non −96%. Spiega da dove viene la differenza guardando le rotte (70 / 15 / 15) e il budget guard.
5. ★★★ Un collega dice: "Il nostro sistema fa risparmiare il 96%". Scrivi tre domande che gli faresti prima di crederci.

## Da ricordare

- Il costo di una chiamata si calcola dai token **contati dal motore**, non stimati.
- Un risparmio che non cambia mai è un rapporto di prezzi, non una misura.
- Il costo locale vero dipende dall'**utilizzo**: sotto una soglia (qui ~12%) il cloud costa meno.
