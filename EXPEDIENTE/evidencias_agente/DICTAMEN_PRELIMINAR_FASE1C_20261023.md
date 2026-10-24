# Dictamen preliminar — LOGOS Fase 1C

- Fecha: 2026-10-23
- Estado: PRUEBAS LIMITADAS SUPERADAS; REVISIÓN HUMANA PENDIENTE
- Alcance: evidencia experimental de TC-03 y TC-06 para los perfiles concretos ensayados.
- No implica aprobación de producción, validación universal del sandbox ni autorización de integración.

## TC-03 — Canario de archivos

- Resultado comunicado por el script: código 0.
- Pre-vuelo: superado.
- Lectura del canario: rechazada por la ruta esperada, según el resultado comunicado.
- SHA-256 del canario inicial: `bf23e47d02c6987ea39d434ebafde3378d06eb786b2f52407491745e4bd4a140`.
- Integridad: hash inicial y final reportados como idénticos.
- Script: `tests/fase1c/test_canary_tc03.sh`
- SHA-256 actual del script: `1499cb1355a150ccb7097f4612cebe3780c15b33b04a0c55a8f77f71983d9fb3`
- Registro de evidencia: `EXPEDIENTE/evidencias_agente/TC03_canario_20261023.json`

Conclusión acotada: se observó la inaccesibilidad del canario seleccionado en esa ejecución y perfil de montaje.

## TC-06 — Aislamiento de red

- Resultado comunicado por el script: código 0.
- Control positivo desde el host: superado.
- Pre-vuelo: superado.
- Conexión desde el namespace aislado: `BLOCKED:ConnectionRefusedError:111`.
- Limpieza: completada, según la salida comunicada.
- Script: `tests/fase1c/test_network_tc06.sh`
- SHA-256 actual del script: `5b0cd232f83e067bd4929d4890224c3b2d386db2c25d03255b3c3fde522b460b`
- Registro de evidencia: `EXPEDIENTE/evidencias_agente/TC06_red_20261023.json`

Conclusión acotada: el cliente en el namespace de red probado no alcanzó el servidor TCP temporal enlazado a `127.0.0.1` del host.

## Consistencia comprobada

- Ambos registros JSON se parsean correctamente.
- Los hashes actuales de ambos scripts coinciden con los guardados en los registros.
- Ambos scripts pasan `bash -n`.
- Los resultados consignados corresponden a los códigos de salida registrados: 0.

## Límites y pendientes

1. Las salidas de terminal aportadas por el Director son la fuente de los resultados experimentales; este documento no sustituye los registros originales.
2. TC-03 no demuestra aislamiento de todos los archivos, interfaces o recursos del host.
3. TC-06 no demuestra aislamiento frente a todas las interfaces, rutas o vías de comunicación.
4. TC-06 no valida aislamiento de archivos, ni TC-03 valida la red: son controles separados.
5. No se ha demostrado contención universal, aislamiento de recursos mediante cgroups ni resistencia frente a todas las clases de ataque.
6. La revisión humana del Director sigue pendiente.
7. Los cuatro artefactos de pruebas y evidencias continúan sujetos a revisión antes de un eventual commit.

## Dictamen

TC-03 y TC-06 cumplen los criterios limitados comunicados por sus scripts en las ejecuciones reportadas. La Fase 1C queda como **pruebas experimentales acotadas superadas, pendientes de revisión humana**. No se declara validado el sandbox completo ni se modifica la raíz de confianza, el manifiesto o el estado de aprobación de LOGOS.
