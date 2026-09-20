#!/bin/bash
# navego-restore — Restaura el último backup funcional.
# Uso: navego-restore

cd ~/navego_recuperado || exit 1

BK=$(ls -td ~/navego_recuperado/backups/FUNCIONAL_* 2>/dev/null | head -1)
if [ -z "$BK" ]; then
  echo "❌ No hay backup FUNCIONAL_* para restaurar."
  echo "   Buscá otro backup manualmente."
  exit 1
fi

echo "═══════════════════════════════════════════"
echo "  NAVEGO — RESTAURACIÓN"
echo "═══════════════════════════════════════════"
echo ""
echo "Restaurando desde: $BK"
echo ""
read -p "¿Continuar? (s/N): " confirm
if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
  echo "Cancelado."
  exit 0
fi

cp "$BK/App.tsx" ./App.tsx 2>/dev/null && echo "✅ App.tsx restaurado"
cp "$BK/MapaOffline.tsx" components/MapaOffline.tsx 2>/dev/null && echo "✅ MapaOffline.tsx restaurado"
[ -d "$BK/maptest" ] && cp -r "$BK/maptest/"* assets/maptest/ 2>/dev/null && echo "✅ Mapas restaurados"

echo ""
echo "✅ Restauración completa."
echo "   Verificá con: navego-check"
