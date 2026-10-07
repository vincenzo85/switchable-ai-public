#!/usr/bin/env bash
# run.sh — entrypoint unico di switchable_ai. Guida: docs/GUIDA-PER-NEGATI.md
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
[ -f .env ] && set -a && . ./.env && set +a

usage() {
  cat << 'USAGE'
switchable_ai — Architettura AI "Switchabile"        (guida: docs/GUIDA-PER-NEGATI.md)

USO: ./run.sh <comando> [argomenti]

  DEMO DEL TALK
  demo                "one request, quattro rotte": decisione + esecuzione reale
  demo-dry            solo le decisioni (JSON), nessun modello chiamato
  route "<prompt>"    decisione di routing per UN prompt
  ask "<prompt>"      esegue UN prompt end-to-end (rotta, fallback, costo)
  stress [N]          stress test di atterraggio (default 100 task)

  RAG LOCALE SDLC
  rag-build           (ri)costruisce l'indice su docs/, wiki/, infra/, kb/ e git log
  rag "<domanda>"     cerca nella knowledge base locale
  ingest <file.md>    il flusso n8n da riga di comando (classifica, estrai, indicizza, QA)

  NUMERI
  report              cockpit: costi, latenze p50/p95, fallback, violazioni residency
  flywheel            esporta le trace anonimizzate → data/flywheel/sft.jsonl
  bench <nome>        tco | compression | vllm | advisor | stress   → benchmarks/results/
  numbers             aggrega i benchmark in talk/numbers.json (unica fonte del deck)

  QUALITÀ
  test                tutta la suite pytest (il gate)
  mutation            mutation testing: sabota il codice, i test DEVONO virare al rosso
  check               test + confini esagonali + mutation

  INFRASTRUTTURA
  serve               API su :8088 (OpenAI-compatible, webhook n8n, /metrics)
  mcp                 server MCP stdio (route_prompt, ask, rag_search, cost_report, stress_test, flywheel_export)
  up [profili]        docker compose (default: core obs n8n) — gateway :4000, Langfuse :3011, Grafana :3012, n8n :5678
  down                ferma lo stack
  deck                apre la presentazione 3D
  deck-redteam        apre il deck red team (la tesi sotto attacco)

  help                questa schermata
USAGE
}

[ $# -ge 1 ] || { usage; exit 0; }
cmd="$1"; shift || true
case "$cmd" in
  demo)       $PY -m app.main demo "$@" ;;
  demo-dry)   $PY -m app.main demo --dry-run ;;
  route|ask|rag) $PY -m app.main "$cmd" "$@" ;;
  stress)     $PY -m app.main stress --n "${1:-100}" --out benchmarks/results/stress_cli.json ;;
  rag-build)  $PY -m app.main rag-build ;;
  ingest)     $PY -m app.main ingest "$@" ;;
  report)     $PY -m app.main report "$@" ;;
  flywheel)   $PY -m app.main flywheel ;;
  bench)      $PY "benchmarks/run_${1:?uso: ./run.sh bench tco|compression|vllm|advisor|stress}.py" "${@:2}" ;;
  numbers)    $PY benchmarks/build_numbers.py ;;
  test)       $PY -m pytest -q ;;
  mutation)   $PY tools/mutation_check.py ;;
  check)      $PY -m pytest -q && $PY -m pytest -q tests/test_architecture_boundaries.py && $PY tools/mutation_check.py ;;
  serve)      $PY -m app.main serve --host "${SAI_HOST:-0.0.0.0}" --port "${SAI_PORT:-8088}" ;;
  mcp)        $PY -m app.main mcp ;;
  up)         profiles=("${@:-core obs n8n}"); args=(); for p in ${profiles[*]}; do args+=(--profile "$p"); done
              docker compose -f infra/docker-compose.yml "${args[@]}" up -d ;;
  down)       docker compose -f infra/docker-compose.yml --profile '*' down ;;
  deck)       [ -f talk/deck/dist/index.html ] || $PY talk/deck/build.py; xdg-open talk/deck/dist/index.html 2>/dev/null || echo "apri talk/deck/dist/index.html" ;;
  deck-redteam) [ -f talk/deck/dist-redteam/index.html ] || $PY talk/deck/build.py --deck redteam; xdg-open talk/deck/dist-redteam/index.html 2>/dev/null || echo "apri talk/deck/dist-redteam/index.html" ;;
  help|-h|--help) usage ;;
  *) echo "comando sconosciuto: $cmd"; usage; exit 1 ;;
esac
