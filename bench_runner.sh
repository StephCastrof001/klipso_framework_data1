#!/bin/bash
# ============================================================================
# bench_runner.sh — Acumulador de evals 24/7
# ============================================================================
# Procesa datasets en bench_queue/, corre Modelo A con Ollama local (gratis),
# captura el eval, y lo ACUMULA en bench_results/accumulated.jsonl.
# Idempotente: dataset ya procesado se salta. Diseñado para cron 24/7.
#
# Estructura:
#   bench_queue/<name>.csv          ← datasets pendientes (drop aquí)
#   bench_queue/<name>.key.md       ← answer key opcional (ground truth)
#   bench_done/<name>.csv           ← ya procesados
#   bench_results/accumulated.jsonl ← un eval por línea, con timestamp
#   bench_results/<name>_<ts>/      ← outputs completos por corrida
# ============================================================================
set -uo pipefail

ROOT="$HOME/klipso_framework_data1"
QUEUE="$ROOT/bench_queue"
DONE="$ROOT/bench_done"
RESULTS="$ROOT/bench_results"
LOCK="/tmp/bench_runner.lock"
LOG="$RESULTS/runner.log"

mkdir -p "$QUEUE" "$DONE" "$RESULTS"

# Singleton — no correr dos a la vez (1 GPU T4)
exec 9>"$LOCK"
flock -n 9 || { echo "[$(date -u +%FT%TZ)] ya corriendo, salgo" >> "$LOG"; exit 0; }

cd "$ROOT" || exit 1
export PYTHONPATH="$ROOT"

ts() { date -u +%Y%m%dT%H%M%SZ; }
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a "$LOG"; }

shopt -s nullglob
processed=0
for csv in "$QUEUE"/*.csv; do
    name="$(basename "$csv" .csv)"
    run_ts="$(ts)"
    out_dir="$RESULTS/${name}_${run_ts}"
    mkdir -p "$out_dir"

    log "BENCH START: $name"

    # Modelo A: single-csv = mismo archivo como main y competition
    if timeout 600 python3 run_pipeline.py \
            --main-csv "$csv" \
            --competition-csv "$csv" \
            --outputs-dir "$out_dir" >> "$out_dir/run.log" 2>&1; then
        status="ok"
    else
        status="error"
    fi

    # Capturar eval si existe
    eval_file="$out_dir/eval.json"
    [ -f "$out_dir/eval.json" ] || eval_file=""

    # Answer key (ground truth) si existe
    key="$QUEUE/${name}.key.md"
    has_key="no"
    [ -f "$key" ] && { has_key="yes"; cp "$key" "$out_dir/answer_key.md"; }

    # Acumular línea en el jsonl maestro
    printf '{"ts":"%s","dataset":"%s","status":"%s","has_answer_key":"%s","out_dir":"%s"}\n' \
        "$run_ts" "$name" "$status" "$has_key" "$out_dir" >> "$RESULTS/accumulated.jsonl"

    log "BENCH DONE: $name → $status (key=$has_key)"

    # Mover dataset a done/ (idempotencia: no re-procesar)
    mv "$csv" "$DONE/" 2>/dev/null
    [ -f "$key" ] && mv "$key" "$DONE/" 2>/dev/null

    processed=$((processed+1))
done

log "RUNNER FIN: $processed datasets procesados"

# Backup a GitHub (supervivencia — Capa 7)
if [ "$processed" -gt 0 ]; then
    git add bench_results/ bench_done/ 2>/dev/null
    git commit -q -m "bench: +$processed evals acumulados ($(date -u +%F))" 2>/dev/null
    git push -q origin main 2>/dev/null && log "PUSH OK" || log "PUSH fallo (revisar)"
fi
