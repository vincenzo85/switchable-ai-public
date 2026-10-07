# 07 — Compressione dei prompt

## Obiettivi

- Capire quando conviene comprimere un prompt (e quando no).
- Capire come funziona una compressione **estrattiva** semplice.
- Distinguere compressione **guidata dalla domanda** e **agnostica**, con numeri misurati.

## Il concetto

Sul cloud si paga a token. Un prompt lungo (un log, un verbale, un documento) contiene molte frasi che non servono per **quella** domanda. Comprimere = mandare meno token mantenendo l'informazione utile.

Due regole del progetto:
1. **Si comprime solo ciò che si paga.** In locale il token costa quasi zero: comprimere aggiunge solo il rischio di perdere informazione. Quindi la compressione si applica **solo alla rotta cloud**, e solo sopra una soglia (`SAI_COMPRESS_THRESHOLD`, default 1.500 token stimati).
2. **Non rompere il prompt caching.** Molti provider fanno pagare meno i prefissi già visti. Se la compressione cambia l'inizio del prompt, la cache non funziona più. Il compressore può lasciare intatti i primi N caratteri (`stable_prefix_chars`).

## Come è fatto qui (`adapters/compression/extractive.py`)

Compressione **estrattiva**: non riscrive, **sceglie** frasi del testo originale.

1. Divide il testo in frasi.
2. Assegna a ogni frase un punteggio:
   - **rarità** delle sue parole nel testo (una frase con parole che compaiono ovunque vale poco);
   - **sovrapposizione con la domanda** (+2 per ogni parola in comune), se la domanda è nota;
   - le frasi **identiche** già viste valgono −1 (duplicati puri).
3. Tiene le frasi migliori finché non raggiunge `keep_ratio` dei caratteri (0,5 in produzione).
4. Le rimette nell'**ordine originale**.

Zero dipendenze, zero GPU, millisecondi.

## Esempio svolto

```python
from adapters.compression.extractive import ExtractiveCompressor

text = ("Il servizio pagamenti gira su tre nodi. I log vengono ruotati ogni notte. "
        "Il backup del database è alle 02:30 ogni giorno. La dashboard mostra le latenze. "
        "Il team on-call cambia il lunedì. I log vengono ruotati ogni notte. "
        "Il certificato TLS scade il 14 novembre. La dashboard mostra le latenze.")
c = ExtractiveCompressor()
for q in ("", "A che ora è il backup del database?"):
    r = c.compress(text, keep_ratio=0.4, question=q)
    print(repr(q[:20]), r.tokens_before, "->", r.tokens_after, "|", r.text)
```

Output:

```
'' 73 -> 28 | Il servizio pagamenti gira su tre nodi. Il team on-call cambia il lunedì. Il certificato TLS scade il 14 novembre.
'A che ora è il backu' 73 -> 30 | Il servizio pagamenti gira su tre nodi. Il backup del database è alle 02:30 ogni giorno. La dashboard mostra le latenze.
```

Senza domanda, la frase sul backup **è stata tagliata**: se poi chiedi l'ora del backup, la risposta non c'è più. Con la domanda, la frase giusta resta. I duplicati ("I log vengono ruotati…") spariscono in entrambi i casi.

## Numeri misurati (`benchmarks/run_compression.py`)

20 prompt "ago nel pagliaio" (un fatto da ritrovare in un contesto lungo):

| Variante | Token risparmiati | Risposte corrette |
|---|---:|---:|
| originale | 0% | 100% |
| estrattiva guidata, 50% | 51% | 100% |
| estrattiva guidata, 30% | 68% | 100% |
| agnostica, 50% | 50% | 75% |
| agnostica, 30% | 68% | 70% |

Stesso risparmio, qualità molto diversa: **sapere la domanda** cambia tutto. Il caso agnostico è quello realistico quando comprimi un contesto **una volta** per molte domande diverse.

Avvertenza scritta nel benchmark: è un compito facile (un fatto, spesso con parole in comune con la domanda). Misura il risparmio, non la qualità in generale. In letteratura: LLMLingua fino a 20× di compressione, CAPC −90% (vedi `docs/BIBLIOGRAFIA.md`).

## Esercizi

1. ★ Ripeti l'esempio con `keep_ratio=0.8`. Quali frasi ricompaiono?
2. ★ Chiedi "quando scade il certificato?" con `keep_ratio=0.4`. La frase giusta resta?
3. ★★ Usa `ExtractiveCompressor(stable_prefix_chars=40)` e verifica che i primi 40 caratteri dell'output coincidano con l'input. Perché è importante per il costo?
4. ★★ Perché `ExecuteRequest` chiama il compressore senza passare la domanda (`question=""`)? Pensa a cosa sia "la domanda" quando il prompt è un unico blocco di testo.
5. ★★★ Progetta un esperimento per misurare se la compressione peggiora le risposte **di ragionamento** (non di ricerca di un fatto). Che metrica useresti?

## Da ricordare

- Comprimi solo dove paghi, e solo sopra una soglia.
- La compressione estrattiva sceglie frasi; con la domanda nota sceglie molto meglio.
- Lascia intatto il prefisso stabile, o perdi lo sconto del prompt caching.
