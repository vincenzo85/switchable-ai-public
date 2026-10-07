"""Set DEV per mettere a punto il router (modalità, descrizioni, doppio ordine).

Separato dal set di TEST (routing_heldout.py), che si usa UNA volta sola a
configurazione scelta. Scritto il 2026-10-04 con la stessa regola del test:
richieste realistiche, senza cercare di proposito le parole chiave delle regole.
Nessun prompt è ripreso dal test.
"""
DEV = [
    # --- local: compiti brevi e ripetitivi
    ("local", "Questa frase è in italiano o in spagnolo? 'Mañana llueve en Madrid'"),
    ("local", "Correggi gli errori di battitura: 'il servr non risponde da ieri sea'"),
    ("local", "Dammi il codice ISO del paese per 'Germania'."),
    ("local", "È una lamentela o un complimento? 'Finalmente un'app che funziona al primo colpo'"),
    ("local", "Metti in ordine alfabetico: pera, mela, banana, kiwi."),
    ("local", "Trasforma in elenco puntato: deploy alle 18, rollback se errori, avvisa il team."),
    ("local", "Che lingua di programmazione è questo frammento? 'fn main() { println!(\"ciao\"); }'"),
    ("local", "Abbrevia in massimo 10 parole: 'la riunione di domani è rimandata a giovedì per assenza del responsabile'"),
    ("local", "Qual è il tono di questa mail, formale o informale? 'Ciao ragazzi, ci vediamo dopo per il caffè'"),
    ("local", "Genera un titolo breve per questo commit: 'aggiunto timeout al client http del gateway'"),
    ("local", "Il numero 4521 è pari o dispari?"),
    ("local", "Scrivi in maiuscolo: 'switchable ai gateway'."),
    # --- cloud: ragionamento complesso, spesso breve
    ("cloud", "Quali rischi vedi nel passare da PostgreSQL a un database a grafo per le raccomandazioni? Argomenta."),
    ("cloud", "Come struttureresti un piano di capacità per un e-commerce che a Natale triplica il traffico?"),
    ("cloud", "Spiega perché un sistema eventualmente consistente può mostrare saldi negativi e come evitarlo."),
    ("cloud", "Scrivi una strategia di test per un motore di pricing con 300 regole che interagiscono."),
    ("cloud", "Che compromessi ci sono tra fine-tuning e RAG per un assistente legale? Raccomanda un approccio."),
    ("cloud", "Individua i colli di bottiglia probabili in una pipeline ETL che rallenta del 40% ogni mese."),
    ("cloud", "Proponi un modello di permessi multi-tenant per un SaaS B2B con gerarchie di reparti."),
    ("cloud", "Come ridurresti del 30% il costo cloud di un cluster Kubernetes senza toccare gli SLA?"),
    ("cloud", "Ragiona sui casi limite di un algoritmo di rate limiting distribuito su tre regioni."),
    ("cloud", "Prepara un piano di risposta a un data breach per una PMI con 50 dipendenti."),
    # --- local_rag: domande sulla NOSTRA documentazione
    ("local_rag", "Che porta usa Grafana nel nostro stack?"),
    ("local_rag", "Perché abbiamo spostato vLLM sulla porta 8010?"),
    ("local_rag", "Quali modelli locali usa il nostro gateway per la rotta fast-local?"),
    ("local_rag", "Cosa prevede la nostra procedura quando una violazione di residency compare in dashboard?"),
    ("local_rag", "Da dove legge il nostro indice i documenti da indicizzare?"),
    ("local_rag", "Che decisione abbiamo preso sull'uso di un LLM come router, e perché?"),
    ("local_rag", "Come si chiamano gli alias che abbiamo configurato su LiteLLM?"),
    ("local_rag", "Qual è la nostra regola per i dati sensibili e chi la può scavalcare?"),
    ("local_rag", "In che ordine valutiamo le regole dure del nostro router?"),
    ("local_rag", "Che cosa misura il nostro pannello 'Turbolenza' in Grafana?"),
    # --- sensibili: il cloud non è ammesso
    ("local", "Riservato: confronta le offerte dei due fornitori di pulizie e indica la più conveniente."),
    ("local", "Analizza le buste paga di settembre e segnala anomalie negli straordinari."),
    ("local", "Strettamente interno: valuta i rischi della fusione con la società Gamma."),
    ("local", "Rispondi a giulia.verdi@example.com sullo stato della sua richiesta di ferie."),
    ("local", "Verifica il codice fiscale VRDGLI85M41F205X nella pratica 2231."),
    ("local", "Confidenziale: riassumi il verbale del consiglio di amministrazione di ieri."),
    ("local", "Ecco la cartella clinica: c'è qualche interazione tra i farmaci elencati?"),
    ("local", "Documento riservato: prepara una sintesi delle trattative sindacali in corso."),
    ("local", "Controlla l'IBAN IT02L1234512345123456789012 del nuovo fornitore."),
    ("local", "Dati personali di Marco Neri: aggiorna l'indirizzo e conferma via mail."),
]
