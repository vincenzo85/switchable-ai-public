# Il 100% che si dà ragione da solo

Il batch di atterraggio e le regole del router li ha scritti la stessa persona, con le stesse parole chiave: 100% di rotte giuste. Su 32 richieste scritte apposta senza quelle parole (`benchmarks/routing_heldout.py`) le regole scendono al 53%. Rizzo Flow e Open-Jev arrivano al 66%.

Due cose da non fare:
- ritoccare le regole finché il set di controllo torna verde: diventerebbe un secondo set di casa;
- presentare il 100% senza il 53%.

Anche Rizzo Flow aveva un "100%" falso al primo giro: 52 errori su 100 erano finiti sulla regola di riserva. Si è scoperto guardando il numero degli errori, non l'accuratezza.
