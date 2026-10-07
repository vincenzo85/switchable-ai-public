# Il firewall scarta il traffico Docker → host

Dai container `host.docker.internal:8088` (API) e `:11434` (Ollama) andavano in timeout: il firewall della macchina scarta il traffico dalla rete bridge di Docker verso l'host, e senza sudo non si cambia.

Soluzione: i servizi che devono chiamare l'host (LiteLLM, Prometheus, Grafana, n8n) usano `network_mode: host` e ascoltano solo su 127.0.0.1. Langfuse resta in bridge, perché è l'host a chiamare lui.

Due trappole collaterali:
- **Langfuse:** Next.js ascolta sull'hostname del container, quindi l'healthcheck deve usare `HOSTNAME=0.0.0.0` e `127.0.0.1` (`localhost` risolve su IPv6).
- **Porte già occupate sull'host:** la 8000 (per questo vLLM è sulla 8010) e la 3001.
