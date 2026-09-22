#!/usr/bin/env bash
# =============================================================================
# run_mision_b.sh — Ejecucion real de la Mision B (corredor SF -> CABA)
# =============================================================================
#
# Este script ejecuta lo que DSH preparo en la Mision A.
# Los parametros son los mismos. Los comandos estan descomentados.
#
# AVISO: este script SI ejecuta. Lee todo antes de correrlo.
# Requiere: ~1 GB libre en disco.
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# CONFIGURACION
# ---------------------------------------------------------------------------
SRC_PBF="$HOME/cockpit/backup_mapa/argentina-260901.osm.pbf"
SRC_SHA256="d43f9af1a293f822fb23da570d7cb44d022b1943e73c79fcd6b87b190b5c504f"
TAGS_FILE="$HOME/navego_recuperado/sandbox_corredor/corridor_tags.txt"

OUTDIR="$HOME/navego_recuperado/sandbox_corredor/out_mision_b"
EXTRACT_PBF="$OUTDIR/corredor_sf_caba.osm.pbf"
FILTERED_PBF="$OUTDIR/corredor_sf_caba_filtrado.osm.pbf"
CORREDOR_GEOJSON="$OUTDIR/corredor_sf_caba.geojsonseq"
MBTILES="$OUTDIR/corredor_sf_caba.mbtiles"
LOG="$OUTDIR/mision_b.log"

BBOX="-61.5439126,-34.7892201,-57.8418874,-31.4390329"

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
log()  { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
fail() { echo "[$(date +%H:%M:%S)] FALLO: $*" | tee -a "$LOG"; exit 1; }

# ---------------------------------------------------------------------------
# PRE-CHEQUEOS
# ---------------------------------------------------------------------------
mkdir -p "$OUTDIR"
echo "=== MISION B — Ejecucion real del corredor SF -> CABA ===" | tee "$LOG"
echo "" | tee -a "$LOG"

log "Paso 0a: verificando herramientas"
command -v osmium      >/dev/null || fail "osmium no encontrado"
command -v tippecanoe  >/dev/null || fail "tippecanoe no encontrado"
osmium --version      | tee -a "$LOG"
tippecanoe --version  | tee -a "$LOG"
echo "" | tee -a "$LOG"

log "Paso 0b: verificando espacio en disco (necesitamos ~1 GB)"
FREE=$(df -BM "$OUTDIR" | awk 'NR==2 {print $4}' | tr -d 'M')
if [ "$FREE" -lt 1024 ]; then
    fail "solo hay ${FREE} MB libres, se necesitan al menos 1024 MB"
fi
log "  espacio libre: ${FREE} MB"

log "Paso 0c: verificando hash del backup"
echo "$SRC_SHA256  $SRC_PBF" | sha256sum -c - 2>&1 | tee -a "$LOG" || \
    fail "hash del backup no coincide, ABORTAR"
echo "" | tee -a "$LOG"

# ---------------------------------------------------------------------------
# PASO 1 — EXTRACCION DEL BBOX
# ---------------------------------------------------------------------------
log "Paso 1: osmium extract (bbox -> $EXTRACT_PBF)"
osmium extract \
    --bbox="$BBOX" \
    --strategy=complete_ways \
    --set-bounds \
    --overwrite \
    --output="$EXTRACT_PBF" \
    --output-format=pbf \
    "$SRC_PBF" 2>&1 | tee -a "$LOG"
log "  extract OK: $(du -h "$EXTRACT_PBF" | cut -f1)"
echo "" | tee -a "$LOG"

# ---------------------------------------------------------------------------
# PASO 2 — FILTRO DE TAGS
# ---------------------------------------------------------------------------
log "Paso 2: osmium tags-filter ($TAGS_FILE)"
if [ ! -f "$TAGS_FILE" ]; then
    fail "no existe $TAGS_FILE, no puedo filtrar"
fi
osmium tags-filter \
    --expressions="$TAGS_FILE" \
    --overwrite \
    --output="$FILTERED_PBF" \
    --output-format=pbf \
    "$EXTRACT_PBF" 2>&1 | tee -a "$LOG"
log "  filtrado OK: $(du -h "$FILTERED_PBF" | cut -f1)"
echo "" | tee -a "$LOG"

# ---------------------------------------------------------------------------
# PASO 3 — CONVERSION A GEOJSON (streaming)
# ---------------------------------------------------------------------------
log "Paso 3: osmium export -> geojsonseq ($CORREDOR_GEOJSON)"
osmium export \
    --output="$CORREDOR_GEOJSON" \
    --output-format=geojsonseq \
    --add-unique-id=counter \
    --format-option=print_record_separator=false \
    --overwrite \
    "$FILTERED_PBF" 2>&1 | tee -a "$LOG"
log "  geojson OK: $(du -h "$CORREDOR_GEOJSON" | cut -f1)"
echo "" | tee -a "$LOG"

# ---------------------------------------------------------------------------
# PASO 4 — GENERACION MBTILES
# ---------------------------------------------------------------------------
log "Paso 4: tippecanoe -> $MBTILES"
tippecanoe \
    -o "$MBTILES" \
    -Z8 -z14 \
    -l corredor \
    -n "Corredor Santa Fe - CABA (RN9)" \
    --drop-densest-as-needed \
    --extend-zooms-if-still-dropping \
    --force \
    "$CORREDOR_GEOJSON" 2>&1 | tee -a "$LOG"
log "  mbtiles OK: $(du -h "$MBTILES" | cut -f1)"
echo "" | tee -a "$LOG"

# ---------------------------------------------------------------------------
# PASO 5 — VERIFICACION
# ---------------------------------------------------------------------------
log "Paso 5: verificacion"
echo "--- Archivos producidos ---" | tee -a "$LOG"
ls -lh "$EXTRACT_PBF" "$FILTERED_PBF" "$CORREDOR_GEOJSON" "$MBTILES" 2>&1 | tee -a "$LOG"
echo "" | tee -a "$LOG"
echo "--- MBTiles: tiles por zoom ---" | tee -a "$LOG"
sqlite3 "$MBTILES" "select zoom_level,count(*) from tiles group by zoom_level;" 2>&1 | tee -a "$LOG"
echo "" | tee -a "$LOG"
echo "--- Hash del MBTiles final ---" | tee -a "$LOG"
sha256sum "$MBTILES" | tee -a "$LOG"
echo "" | tee -a "$LOG"

log "MISION B COMPLETA. Log: $LOG"
echo "Recorda: revisar los tamaños reales contra size_estimates.csv." | tee -a "$LOG"
