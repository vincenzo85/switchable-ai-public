# Immagini del deck, slide per slide

Generato da `talk/deck/build.py` leggendo il campo `img` di ogni slide in `talk/deck/src/slides.js`.
Per usare un'immagine: salvarla come `talk/assets/img/<id>.webp` (o .jpg/.png), 16:9, almeno 1920×1080,
lato sinistro scuro e vuoto (lì va il titolo). Poi `make deck`: il deck la usa come fondale da solo.

Stile comune (già incluso nei prompt): notte, blu quasi nero, luci avorio, accenti verde acqua / arancio / blu,
composizione minimale, molto spazio negativo a sinistra, niente testo, niente loghi, niente volti.

| # | Fase | Slide | id | Stato | Cosa mostrare | Alternativa SVG/3D |
|---|---|---|---|---|---|---|
| 1 | boarding | Chi decide la rotta? | `finestrino` | da generare | Finestrino di un aereo di notte, luci di una città lontana sotto, ala appena visibile. | 3D già presente: finestrino ovale con nuvole di particelle. |
| 2 | boarding | Un litro di latte | `latte` | da generare | Una bottiglia di latte, sola, illuminata come un oggetto prezioso su un banco di minimarket notturno. | SVG: bottiglia stilizzata a linea avorio, contorno che si disegna. |
| 3 | boarding | Un jet | `jet-parcheggio` | da generare | Un aereo di linea parcheggiato davanti a un minimarket di quartiere, scala assurda, notte. | 3D: particelle che formano la sagoma di un jet sopra il piazzale. |
| 4 | boarding | Anche quando basta camminare | `passi` | da generare | Impronte di passi su un marciapiede bagnato che portano alla porta del negozio, a pochi metri. | SVG: impronte che compaiono una alla volta. |
| 5 | boarding | La promessa: il boarding pass (WOW) | `biglietto` | — | Nessuna foto: il biglietto è disegnato dalle particelle e poi appare in 3D. | Già realizzato: formazione "pass" + card CSS 3D. |
| 6 | briefing | Il patto: misurato, dichiarato, dal vivo | `patto` | da generare | Tre strumenti di bordo su un pannello di cockpit: un righello/scala, un documento timbrato, una spia rossa ON AIR. | Icone (già presenti) che si accendono una alla volta. |
| 7 | briefing | Vi mostrerò un 96%. Non fidatevi. | `avviso` | da generare | Un cartello di avvertimento aeroportuale giallo, sfocato, "attenzione al gradino". | Icona triangolo di avviso che pulsa una volta. |
| 8 | briefing | Quanto costa davvero un task? | `scontrino` | da generare | Uno scontrino lunghissimo che esce da una stampante, con righe di token invece di prodotti. | SVG: scontrino che si srotola, righe che compaiono. |
| 9 | gate | In produzione restano a terra | `tabellone` | da generare | Tabellone partenze reale, tutto rosso: DELAYED/CANCELLED, aeroporto vuoto di notte. | Già realizzato: tabellone split-flap animato. |
| 10 | decollo | Una riga | `porta` | da generare | Una porta d'imbarco chiusa con una sola luce sopra: dietro, rumore di motori diversi. | SVG: una porta da cui escono tre linee colorate (locale/cloud/RAG). |
| 11 | decollo | Chi decide? (WOW: routing) | `torre` | — | Nessuna foto: è il momento del 3D (torre, tre piste che si aprono, quattro richieste). | Già realizzato nel motore. |
| 12 | decollo | La torre non è un LLM | `controllore` | da generare | Il controllore di volo umano davanti agli schermi radar, di spalle, regole scritte a pennarello sul vetro. | Icona robot barrato + torre 3D con la pista cloud sbarrata (già realizzato). |
| 13 | decollo | Quattro regole dure | `regole` | da generare | Quattro cartelli aeroportuali luminosi in fila: lucchetto, casa, salvadanaio, cervello. | Tessere-icona già presenti. |
| 14 | crociera | Una richiesta | `nastro` | da generare | Un nastro bagagli in un aeroporto vuoto con una sola valigia luminosa che viaggia. | Già realizzato: lo schema si costruisce e un pacchetto viaggia sul globo. |
| 15 | crociera | Demo: quattro destini | `demo` | — | Nessuna foto: demo dal vivo sul globo. | Già realizzato. |
| 16 | crociera | 96% | `novantasei` | — | Nessuna foto: il numero gigante da solo. | — |
| 17 | crociera | La stiva | `stiva` | da generare | Stiva di un aereo cargo con scaffali di faldoni e una luce blu: i documenti restano a bordo. | Già realizzato: le richieste entrano nel globo. |
| 18 | crociera | Una catena, non una chat | `catena` | da generare | Un nastro trasportatore notturno con documenti che passano sotto quattro stazioni luminose. | Flusso di icone (già presente). |
| 19 | crociera | Sabotaggi scoperti | `sabotaggio` | da generare | Un tecnico di notte che stacca un cavo in un hangar e una spia rossa che si accende subito. | Icona bug barrato con contatore. |
| 20 | crociera | Il cockpit | `cockpit` | — | Screenshot vero di Grafana (già presente). | Già realizzato. |
| 21 | crociera | La scatola nera | `scatola-nera` | da generare | La scatola nera arancione di un aereo, su un tavolo di laboratorio. | Screenshot Langfuse (già presente) + icona euro. |
| 22 | crociera | Comprimere è buttare | `valigia` | da generare | Una valigia sottovuoto schiacciata con un passaporto lasciato fuori sul pavimento. | Icona pacco + due numeri a confronto. |
| 23 | crociera | Il carico sceglie il motore | `motori` | da generare | Due motori d'aereo sul banco prova: uno piccolo acceso, uno grande con tante bocchette. | Icona tachimetro + numero. |
| 24 | crociera | Due correzioni banali | `forbici` | da generare | Forbici che tagliano un faldone esattamente lungo i separatori di sezione. | Icona forbici + numero. |
| 25 | crociera | Il router perfetto non esiste | `radar` | da generare | Schermo radar con metà dei puntini dentro il bersaglio e metà fuori. | Icona lista + numero. |
| 26 | crociera | Un modello piccolo, ben istruito | `secondo-controllore` | da generare | Due postazioni in torre: un controllore e, accanto, una piccola console luminosa che suggerisce. | Barre (già presenti). |
| 27 | turbolenza | Jet di cartone | `cartone` | da generare | Un modellino d'aereo di cartone appeso a un filo davanti a un cielo dipinto. | Icona aereo + scatola. |
| 28 | turbolenza | 100 richieste (WOW: turbolenza) | `turbolenza` | — | Nessuna foto: replay animato. | Già realizzato. |
| 29 | atterraggio | Una GPU ferma costa più del cloud | `gpu-ferma` | da generare | Una scheda GPU spenta in un rack buio, coperta di polvere, con un cartellino del prezzo. | Icona CPU + pausa. |
| 30 | atterraggio | Il pareggio | `pareggio` | da generare | Una bilancia a due piatti in equilibrio: un chip da una parte, una nuvola dall'altra. | Barre con linea del cloud (già presenti). |
| 31 | atterraggio | Ho trovato | `scoperte` | da generare | Una bacheca di sughero con quattro foto polaroid fissate con puntine. | Tessere-icona (già presenti). |
| 32 | atterraggio | Non dicono | `limiti` | da generare | Una mappa nautica con zone in bianco marcate "terra incognita". | Tessere-icona (già presenti). |
| 33 | atterraggio | Ogni volo migliora il prossimo | `volano` | — | Nessuna foto: il volano 3D con le tracce in orbita. | Già realizzato. |
| 34 | atterraggio | Finale (WOW) | `finale` | — | Nessuna foto: il volano collassa nella torre. | Già realizzato. |
| 35 | arrivi | Domande | `arrivi` | da generare | La sala arrivi di notte, porte scorrevoli aperte, luce calda. | QR e titolo (già presenti). |
| 36 | appendice | Appendice · Per chi: i passeggeri | `—` | — |  |  |
| 37 | appendice | Appendice · Tecnologie e perché | `—` | — |  |  |
| 38 | appendice | Appendice · Cosa dice la ricerca | `—` | — |  |  |
| 39 | appendice | Appendice · MCP | `—` | — |  |  |
| 40 | appendice | Appendice · Ollama e vLLM | `—` | — |  |  |
| 41 | appendice | Appendice · Compressione | `—` | — |  |  |

## Prompt per la generazione

### 1. Chi decide la rotta? — `finestrino`

```
airplane window at night seen from the seat, distant city lights below, wing tip barely visible, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 2. Un litro di latte — `latte`

```
a single glass bottle of milk on an empty corner-shop counter at night, dramatic spotlight, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 3. Un jet — `jet-parcheggio`

```
a huge airliner parked in a small neighbourhood corner-shop parking lot at night, absurd scale, wet asphalt reflections, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 4. Anche quando basta camminare — `passi`

```
footprints on a wet sidewalk leading a few meters to a lit shop door at night, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 6. Il patto: misurato, dichiarato, dal vivo — `patto`

```
three glowing cockpit instruments side by side: a measuring gauge, a stamped checklist, a red ON AIR light, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 7. Vi mostrerò un 96%. Non fidatevi. — `avviso`

```
a yellow airport caution sign out of focus in a dark terminal, single warm light, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 8. Quanto costa davvero un task? — `scontrino`

```
an endless paper receipt curling out of a small printer in the dark, abstract lines instead of items, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 9. In produzione restano a terra — `tabellone`

```
airport departures board at night with every flight marked delayed or cancelled in red and amber, empty terminal, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 10. Una riga — `porta`

```
a single closed boarding gate door with one light above it, hint of different aircraft silhouettes behind glass, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 12. La torre non è un LLM — `controllore`

```
an air traffic controller seen from behind in a dark tower cab, radar screens, rules handwritten on the glass, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 13. Quattro regole dure — `regole`

```
four illuminated airport wayfinding signs in a row in a dark corridor, simple pictograms, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 14. Una richiesta — `nastro`

```
a single glowing suitcase travelling on an empty airport baggage conveyor at night, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 17. La stiva — `stiva`

```
inside an aircraft cargo hold filled with neatly shelved document boxes, cold blue light, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 18. Una catena, non una chat — `catena`

```
an automated conveyor line at night passing documents under four glowing stations, industrial, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 19. Sabotaggi scoperti — `sabotaggio`

```
a night maintenance hangar, a hand unplugging a cable while a red warning light instantly turns on, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 21. La scatola nera — `scatola-nera`

```
an orange aircraft flight recorder black box on a dark lab table, single spotlight, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 22. Comprimere è buttare — `valigia`

```
a vacuum-compressed suitcase squeezed flat, a passport left behind on the floor next to it, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 23. Il carico sceglie il motore — `motori`

```
two jet engines on a test stand at night, one small, one large, heat haze, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 24. Due correzioni banali — `forbici`

```
scissors cutting a thick binder exactly along its colored section dividers, top light, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 25. Il router perfetto non esiste — `radar`

```
a round radar screen where half of the blips land on target and half drift outside, green phosphor, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 26. Un modello piccolo, ben istruito — `secondo-controllore`

```
two workstations in an air traffic control tower at night, one with a small glowing assistant console beside the main radar, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 27. Jet di cartone — `cartone`

```
a cardboard model airplane hanging on a string in front of a painted stormy sky, theatre lighting, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 29. Una GPU ferma costa più del cloud — `gpu-ferma`

```
an idle powered-off GPU card in a dark server rack with a hanging price tag, dust in the light beam, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 30. Il pareggio — `pareggio`

```
a balance scale in perfect equilibrium, a computer chip on one pan, a small cloud on the other, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 31. Ho trovato — `scoperte`

```
a cork board with four polaroid photos pinned on it, red string between them, dim light, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 32. Non dicono — `limiti`

```
an old navigation chart with blank unmapped areas, a compass resting on it, low light, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

### 35. Domande — `arrivi`

```
airport arrivals hall at night, sliding doors open, warm light spilling out, empty, cinematic night photography, deep navy almost black background (#05060A), ivory highlights, accent lights teal #199e70, orange #d95926, blue #3987e5, minimal composition, large negative space on the left for a headline, 16:9, no text, no logos, no people faces
```

