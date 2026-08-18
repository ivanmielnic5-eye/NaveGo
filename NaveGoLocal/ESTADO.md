# Estado del Proyecto NaveGoLocal

Última actualización: 16 de agosto de 2026

## Resumen general

NaveGoLocal es una app náutica offline-first con HUD Glass Nautical Dark.
Combina tracking GPS, persistencia local SQLite, sincronización a PC para Godot y alertas de proximidad simuladas.

## Estado actual por módulos

| Módulo | Estado | Observaciones |
|---|---|---|
| HUD / UI | ✅ Estable | Estética glass dark, botón CENTRAR arriba izquierda, mapa oscuro |
| Mapa portrait | ✅ Estable | Altura 190, borde cian, indicador de usuario activo |
| Mapa landscape | ✅ Estable | Pantalla completa, sin paneles, solo CENTRAR y GPS badge |
| Tracker GPS | ⚠️ Requiere ajuste | Caminata fantasma y rumbo errático. Pendiente máquina de estados |
| SQLite | ✅ Funcionando | Tablas sessions y gps_fixes. Insert, start, end OK |
| Sincronización a PC | ✅ Funcionando | Servidor simulate.js recibe datos en puerto 3000 |
| Godot | ✅ Funcionando | Renderiza trayectoria desde JSON |
| Alertas de proximidad | 🟡 Simuladas | Zonas fijas en useNaveGoTracker.ts |

## Próximos pasos

1. Implementar máquina de estados GPS (GPS_OK, DEGRADED, LOST, RECOVERING)
2. Filtrar rumbo errático y caminata fantasma
3. Crear pantalla de historial de sesiones
4. Decision Engine con alertas reales desde SQLite
5. Integración completa con Godot (hazards reales)

## Decisiones de arquitectura

- Formato de pantalla: portrait principal, landscape solo mapa a pantalla completa.
- Botón CENTRAR: esquina superior izquierda en ambos modos.
- Sin API key de Google Maps por ahora (desarrollo con Expo Go).
- Sin Git (se usa EAS_NO_VCS=1 para builds).

## Comandos útiles

```powershell
# Levantar Metro en puerto 8081 con LAN
cd C:\Users\ivan\Downloads\NaveGoLocal
$env:EXPO_NO_FAST_REFRESH = "1"
npx expo start --lan --clear --port 8081

# Liberar puerto 8081 si está ocupado
$connection = Get-NetTCPConnection -LocalPort 8081 -State Listen -ErrorAction SilentlyContinue
if ($connection) { Stop-Process -Id $connection.OwningProcess -Force }

# Desactivar hibernación
powercfg /hibernate off