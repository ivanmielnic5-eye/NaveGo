#!/bin/bash
# navego-check — Verifica el estado del proyecto antes de trabajar.
# Uso: navego-check

cd ~/navego_recuperado || exit 1

echo "═══════════════════════════════════════════"
echo "  NAVEGO — VERIFICACIÓN DE ESTADO"
echo "═══════════════════════════════════════════"
echo ""

# 1. Estado del repo
echo "▸ 1. Estado del repo:"
DIRTY=$(git status --short)
if [ -z "$DIRTY" ]; then
  echo "   ✅ Limpio"
else
  echo "   ⚠️  Hay cambios sin commitear:"
  echo "$DIRTY" | sed 's/^/      /'
fi
echo ""

# 2. ¿App.tsx apunta a la app real?
echo "▸ 2. App.tsx:"
if grep -q "TestMapLibre" App.tsx 2>/dev/null; then
  echo "   ❌ ALERTA: App.tsx apunta a TestMapLibre (test)"
  echo "      Fix: cp App.tsx.bak_test_u08 App.tsx  (o git checkout App.tsx)"
else
  echo "   ✅ Apunta a la app real"
fi
echo ""

# 3. ¿Los mapas grandes están donde deben?
echo "▸ 3. Mapas en assets/maptest/:"
for f in santa_fe.mbtiles render_big.mbtiles; do
  if [ -f "assets/maptest/$f" ]; then
    SIZE=$(du -h "assets/maptest/$f" | cut -f1)
    echo "   ✅ $f ($SIZE)"
  else
    echo "   ❌ FALTA: $f"
    echo "      Buscar en: find ~ -name '$f' 2>/dev/null"
  fi
done
echo ""

# 4. ¿MapaOffline apunta a cuál?
echo "▸ 4. MapaOffline apunta a:"
grep -E "^const DB_NAME" components/MapaOffline.tsx | head -1 | sed 's/^/   /'
echo ""

# 5. Último commit
echo "▸ 5. Último commit:"
git log --oneline -1 | sed 's/^/   /'
echo ""

# 6. Último backup funcional
echo "▸ 6. Último backup funcional:"
BK=$(ls -td ~/navego_recuperado/backups/FUNCIONAL_* 2>/dev/null | head -1)
if [ -n "$BK" ]; then
  echo "   $BK"
else
  echo "   ⚠️  No hay backups FUNCIONAL_*"
fi
echo ""

echo "═══════════════════════════════════════════"
echo "  Si todo dice ✅, podés trabajar."
echo "  Si algo dice ❌, PARAR y avisar."
echo "═══════════════════════════════════════════"
