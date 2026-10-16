#!/usr/bin/env bash
# ============================================================
# run_headless.sh — Wrapper para corridas headless de Godot
# ============================================================
# Uso: ./run_headless.sh <comandos_in.json>
#
# Responsabilidades:
#   1. Validar que comandos_in.json existe
#   2. Crear run_id con timestamp
#   3. Crear carpeta aislada ~/.logos/runs/<run_id>/
#   4. Copiar comandos_in.json
#   5. Exportar NAVEGO_RUN_DIR
#   6. Lanzar Godot headless con timeout de pared
#   7. Reportar código de salida y contenido de la carpeta

INPUT_FILE="$1"
if [ -z "$INPUT_FILE" ]; then
    echo "uso: $0 <comandos_in.json>"
    exit 1
fi

INPUT_FILE="$(realpath "$INPUT_FILE" 2>/dev/null)"
if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: no existe el archivo $INPUT_FILE"
    exit 1
fi

RUN_ID="$(date +%Y%m%d_%H%M%S)_test"
RUN_DIR="$HOME/.logos/runs/$RUN_ID"

if [ -e "$RUN_DIR" ]; then
    echo "ERROR: ya existe $RUN_DIR"
    exit 1
fi

mkdir -p "$RUN_DIR"
cp "$INPUT_FILE" "$RUN_DIR/comandos_in.json"

echo "[run_headless] run_id=$RUN_ID"
echo "[run_headless] run_dir=$RUN_DIR"

export NAVEGO_RUN_DIR="$RUN_DIR"
export NAVEGO_RUN_TIMEOUT_MS="${NAVEGO_RUN_TIMEOUT_MS:-120000}"

echo "[run_headless] lanzando godot headless..."
timeout 180 godot --headless --path "$HOME/interfaz"
CODIGO=$?

echo "[run_headless] godot termino con codigo $CODIGO"
echo "[run_headless] contenido de run_dir:"
ls -la "$RUN_DIR"

if [ -f "$RUN_DIR/runner.log" ]; then
    echo "[run_headless] ultimas 10 lineas de runner.log:"
    tail -10 "$RUN_DIR/runner.log"
fi

if [ -f "$RUN_DIR/resultado.json" ]; then
    echo "[run_headless] resultado.json:"
    cat "$RUN_DIR/resultado.json"
fi

exit $CODIGO
