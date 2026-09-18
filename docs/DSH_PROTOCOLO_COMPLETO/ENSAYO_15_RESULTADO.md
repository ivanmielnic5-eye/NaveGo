# Ensayo 15 — Inspección sobre NaveGo real
**Fecha:** 18 sep 2026
**Estado:** VERIFICADO

## Hipótesis
DSH puede orientarse en un repo real que nunca vio,
localizar código específico y reportar sin modificar nada.

## Setup
- Copia aislada de NaveGo en ~/navego_dsh_test (sin android, sin node_modules)
- Wrapper adaptado
- Tarea: encontrar el código del "compass" del mapa

## Resultado
- Detectó que NO existe compass nativo de MapLibre
- Encontró OrientationIndicator en App.tsx:55-97
- Encontró render en App.tsx:366-371
- Detectó que el acelerómetro está comentado (línea 131)
- Mapeó elementos superpuestos (CENTRAR, chip GPS, zIndex:10)
- Propuso 4 opciones de desactivación con líneas exactas
- Advirtió sobre archivos .bak_* residuales

## Verificación
- git status: solo run_ensayo.sh (nuestro wrapper)
- NO modificó ningún archivo del repo
- Duración: 28s
- Eventos en trace: 83

## Capacidad demostrada
Navegación autónoma de repo desconocido + precisión de líneas
+ análisis de superposiciones + corrección de premisa errónea.

## Conclusión
DSH está listo para trabajar sobre NaveGo real en branch aislado.
