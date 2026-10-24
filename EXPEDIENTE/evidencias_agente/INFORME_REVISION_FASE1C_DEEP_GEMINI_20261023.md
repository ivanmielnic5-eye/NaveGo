# Informe para revisión externa — LOGOS Fase 1C
## Revisión de TC-03 y TC-06 para DeepSeek y Gemini

**Fecha:** 2026-10-23  
**Estado:** pruebas acotadas con resultados favorables; revisión humana pendiente.  
**Repositorio:** `~/navego_recuperado`  
**Política:** no modificar la raíz de confianza, el manifiesto ni la aprobación global de LOGOS como consecuencia automática de estas pruebas.

## 1. Objetivo

Solicitar una auditoría independiente del diseño, los resultados y los límites de las pruebas del sandbox de Bubblewrap. Se busca distinguir evidencia observada, inferencias justificadas y afirmaciones aún no demostradas.

## 2. TC-03 — Canario de archivos

**Script:** `tests/fase1c/test_canary_tc03.sh`  
**SHA-256 actual:** `1499cb1355a150ccb7097f4612cebe3780c15b33b04a0c55a8f77f71983d9fb3`  
**Registro existente:** `EXPEDIENTE/evidencias_agente/TC03_canario_20261023.json`

Resultado presentado desde Konsole:
- Pre-vuelo de Bubblewrap y lectura del control: superados.
- Lectura del canario no expuesto: rechazada.
- SHA-256 inicial y final del canario: idénticos.
- Código de salida: `0`.

La comprobación local posterior confirmó que el JSON es válido, que su hash coincide con el script actual y que el script pasa `bash -n`.

**Alcance:** una ejecución, un canario aleatorio y el perfil de montaje concreto. No acredita el aislamiento de todos los archivos del host ni resistencia ante todas las clases de ataque.

## 3. TC-06 — Aislamiento de red, versión inicial

**Script:** `tests/fase1c/test_network_tc06.sh`  
**SHA-256:** `5b0cd232f83e067bd4929d4890224c3b2d386db2c25d03255b3c3fde522b460b`  
**Registro existente:** `EXPEDIENTE/evidencias_agente/TC06_red_20261023.json`

Resultado presentado desde Konsole:
- El host alcanzó el servidor TCP temporal.
- Pre-vuelo dentro del sandbox: superado.
- Conexión desde el namespace aislado: `BLOCKED:ConnectionRefusedError:111`.
- Limpieza: completada, según la salida.
- Código de salida: `0`.

La prueba se limita al servidor enlazado a `127.0.0.1` del host. No acredita aislamiento de todas las interfaces, rutas, puertos o canales de comunicación.

## 4. TC-06 — Versión v2

**Script ejecutado:** `tests/fase1c/test_network_tc06_v2.sh`  
**SHA-256 del script ejecutado:** `b4ffbea464bb8f27d133c2db7cfa3d21ae4c30692546068d8de9ea5a8f15e8f1`

Cambios frente a la versión inicial:
- El timeout deja de aceptarse como resultado de bloqueo.
- Se repite el control positivo desde el host después del intento aislado.
- Se conserva la separación entre fallo de infraestructura, resultado no atribuible y conexión alcanzada.

Resultado presentado desde Konsole:
- Control positivo previo: superado.
- Pre-vuelo: superado.
- Control positivo posterior: superado.
- Cliente aislado: `BLOCKED:ConnectionRefusedError:111`.
- Limpieza: completada, según la salida.
- Código de salida: `0`.

**Defecto menor detectado:** el mensaje del control positivo posterior imprimió literalmente `\\n` en vez de un salto de línea. No altera el resultado de conexión reportado, pero demuestra que el formato de salida necesita corregirse antes de considerar definitiva la implementación del módulo.

La versión inicial y su evidencia se conservan sin sobrescribir.

## 5. Consistencia local verificada

- Los registros originales TC-03 y TC-06 se leen como JSON válidos.
- Los hashes de esos scripts coinciden con sus registros.
- Los hashes de TC-06 v1 y v2 coinciden con los valores previamente observados.
- Los scripts TC-06 v1 y v2 pasan `bash -n`.
- La salida reportada para TC-03 y TC-06 v1/v2 muestra código de salida `0`.
- Los resultados experimentales provienen de transcripciones de Konsole proporcionadas por el Director; este informe no afirma que el sistema de revisión haya ejecutado independientemente las pruebas.

## 6. Conclusión provisional

TC-03 y TC-06 v1/v2 cumplen los criterios acotados comunicados por sus scripts en las ejecuciones reportadas. La conclusión adecuada es:

**PRUEBAS EXPERIMENTALES ACOTADAS SUPERADAS; VALIDACIÓN GLOBAL DEL SANDBOX PENDIENTE.**

No se ha demostrado:
- aislamiento universal de archivos o red;
- aplicación efectiva de límites de CPU, memoria y procesos mediante cgroups;
- resistencia frente a todos los vectores de escape o escalada;
- aptitud para producción;
- autorización para cambiar la raíz de confianza o aprobar globalmente la implementación.

Los cinco artefactos originales de TC-03, TC-06 y el dictamen preliminar permanecen sin commit, según la salida de Git compartida. No se ha hecho commit.

## 7. Preguntas concretas para la auditoría externa

Solicitamos que DeepSeek y Gemini respondan por separado, sin modificar ni ejecutar código:

1. ¿Los criterios de aceptación de TC-03 identifican de forma inequívoca un rechazo de lectura del canario, sin confundirlo con un fallo de infraestructura?
2. ¿La prueba TC-06 demuestra el aislamiento pretendido o queda alguna ambigüedad en la interpretación de `ConnectionRefusedError`?
3. ¿Detectan problemas de limpieza, manejo de errores, namespaces, montajes o posibles falsos positivos en los scripts?
4. ¿Qué pruebas adicionales mínimas consideran necesarias para cgroups y contención de recursos?
5. ¿Qué cambios recomiendan antes de integrar los módulos en `.logos/bin/` o considerar una autorización más amplia?
6. Clasifiquen cada observación como **defecto demostrado**, **riesgo plausible** o **prueba pendiente**. No infieran aprobación humana por silencio.

**Restricción:** esta solicitud es de auditoría y recomendaciones. No se autoriza a los revisores a ejecutar los scripts, modificar el repositorio, actualizar el manifiesto ni alterar la raíz de confianza.
