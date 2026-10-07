# Le parole delle rotte contano più dei trucchi

Per migliorare il secondo controllore (Rizzo Flow) ho provato tre leve sul set DEV:
- la modalità `fallback`;
- il doppio ordine dei candidati, contro il bias di posizione;
- le descrizioni delle rotte.

Solo le descrizioni hanno spostato il risultato: dal 60% all'86% sul dev, dal 66% al 78% sul test misurato una volta. La frase che ha fatto la differenza: "usa il cloud quando serve ragionare, *anche se la domanda è breve*".

Due lezioni:
1. **Dev e test separati, sempre.** Il test l'avevo già visto (sapevo dove sbagliavano le regole). Ritoccare regole o descrizioni guardandolo avrebbe prodotto un numero falso.
2. **Un prompt non si trasferisce gratis tra modelli.** Le stesse descrizioni peggiorano Open-Jev (dal 66% al 56%) e gli fanno mandare 6 richieste in cloud senza motivo.
