# La guardia di confine confrontava per prefisso

Il test di confine del template `hexainit` ammetteva un import se il modulo *iniziava* con uno dei nomi della stdlib in allowlist. `requests` passava perché inizia con `re`. Inoltre l'allowlist elencava solo 14 moduli, quindi `math` o `time` erano vietati nel core senza motivo.

Correzione: confronto esatto sul modulo di primo livello contro `sys.stdlib_module_names`, più un test di regressione. Va riportata anche in `hexainit/template`.
