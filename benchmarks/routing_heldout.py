"""Set di controllo per il routing: richieste scritte SENZA usare di proposito
le parole chiave delle regole. Serve a misurare se il router generalizza o
se il 100% sul batch di atterraggio è solo l'autore che si dà ragione.

Rotta attesa: la più economica che risponde bene. Per i dati sensibili il
cloud non è ammesso: attesa `local`.
"""
HELDOUT = [
    # --- local: compiti brevi e ripetitivi, formulati senza "classifica"/"estrai"
    ("local", "A quale reparto va girata questa segnalazione: 'il badge non apre la porta del magazzino'?"),
    ("local", "Dimmi se questa recensione è positiva o negativa: 'consegna lenta ma prodotto ottimo'."),
    ("local", "Tira fuori data e importo da: 'Bonifico del 4 maggio, 1.250 euro, causale affitto'."),
    ("local", "Questa mail è spam? 'Hai vinto un iPhone, clicca qui per riscattarlo'"),
    ("local", "Traduci in inglese: 'il deploy è fallito per un timeout del database'."),
    ("local", "Riscrivi in tono formale: 'ci becchiamo domani per sistemare il bug'."),
    ("local", "Sintetizza in una riga: 'il server è ripartito dopo l'aggiornamento del kernel e i servizi sono tornati su'."),
    ("local", "Che priorità daresti, alta media o bassa, a: 'il sito è giù per tutti i clienti'?"),
    ("local", "Quali nomi propri ci sono in: 'Marco ha incontrato Giulia a Torino'?"),
    ("local", "Converti in JSON: nome Anna, età 34, città Bari."),
    # --- cloud: ragionamento complesso, spesso in poche parole
    ("cloud", "Confronta Kafka e RabbitMQ per un sistema di ordini con picchi di 50k messaggi al secondo e "
              "requisiti exactly-once: quale sceglieresti e perché, con i rischi?"),
    ("cloud", "Scrivi un piano di migrazione da Oracle a PostgreSQL per 40 microservizi senza downtime."),
    ("cloud", "Perché il nostro servizio ha latenza p99 alta solo il lunedì mattina? Formula tre ipotesi "
              "verificabili e come testarle."),
    ("cloud", "Disegna lo schema di sicurezza zero-trust per un'app bancaria con accesso da partner esterni."),
    ("cloud", "Valuta pro e contro di passare a un monorepo per 12 team, considerando CI, ownership e rilasci."),
    ("cloud", "Proponi un'architettura RAG multi-tenant con isolamento dei dati tra clienti e costi sotto controllo."),
    ("cloud", "Dimostra perché questo lock distribuito basato su timeout può violare la mutua esclusione e "
              "proponi una correzione."),
    ("cloud", "Pianifica la capacità GPU per servire 2 milioni di richieste al giorno con p95 sotto 2 secondi."),
    # --- local_rag: domande sulla NOSTRA documentazione, senza dire "documentazione"
    ("local_rag", "Cosa dobbiamo fare quando il budget del cloud finisce?"),
    ("local_rag", "Qual è la procedura di rilascio che seguiamo noi?"),
    ("local_rag", "Secondo le nostre ADR, perché il router non usa un LLM?"),
    ("local_rag", "Su che porta gira Langfuse da noi?"),
    ("local_rag", "Chi fa da advisor di rotta nel nostro sistema e in che modalità parte di default?"),
    ("local_rag", "Come si ricostruisce l'indice della knowledge base?"),
    ("local_rag", "Quali dei nostri servizi girano in network_mode host e perché?"),
    ("local_rag", "Dove finiscono i documenti che arrivano dal workflow n8n?"),
    # --- dati sensibili: il cloud non è ammesso
    ("local", "Analizza il contratto riservato con il fornitore Beta e trova le clausole rischiose."),
    ("local", "Valuta la situazione del dipendente con stipendi arretrati e proponi una soluzione."),
    ("local", "Ecco la cartella clinica del paziente: quali esami andrebbero fatti per primi?"),
    ("local", "Strettamente interno: riassumi le valutazioni di performance del team vendite."),
    ("local", "Scrivi a mario.rossi@example.com una risposta sul rimborso della pratica 4471."),
    ("local", "Controlla se l'IBAN IT60X0542811101000000123456 corrisponde al fornitore registrato."),
]
