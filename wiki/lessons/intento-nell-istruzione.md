# L'intento sta nell'istruzione, non nel documento

Al primo run reale di n8n il prompt "Classifica questo documento… <corpo di un ADR>" è finito sulla rotta RAG: il corpo conteneva "documentazione" e "repository". Un'estrazione di metadati da 600 caratteri è andata in cloud per sola lunghezza.

Correzioni:
- il tipo di task si legge dal primo paragrafo;
- a parità di tipi vince la parola chiave che compare prima;
- confini di parola, così "rag" non scatta in "paragrafo";
- soglia di lunghezza 5 volte più alta per classificare ed estrarre;
- i dati sensibili si cercano invece su tutto il testo.

I test sintetici non l'avevano visto: sono stati i dati veri a trovarlo.
