# PENDIENTES ABIERTOS — registro institucional

**Creado:** 2026-10-14 (D-2026-0013)
**Regla:** ninguna propuesta que requiera aprobacion del Director
queda olvidada por avance del workflow. Sin respuesta explicita,
sigue pendiente. La IA detecta, registra y recuerda; no aprueba.

Estados posibles: PENDIENTE_DE_LECTURA | PENDIENTE_DE_APROBACION |
APROBADO | RECHAZADO | DIFERIDO (con motivo y condicion de revision).

---

## PENDIENTES ACTIVOS

### P1 — D-B "No-olvido de pendientes"
- Estado: APROBADO (D-2026-0013, 2026-10-14).
- Ubicacion: `.logos/decisions/D-2026-0013.json`.
- Cerrado.

### P2 — D-A "Auditar Entrenador antes de entrenar"
- Estado: APROBADO (D-2026-0012, 2026-10-14).
- Ubicacion: `.logos/decisions/D-2026-0012.json`.
- Cerrado.

### P3 — D-C "Comparaciones justas antes de auditar"
- Estado: APROBADO (D-2026-0014, 2026-10-14).
- Ubicacion: `.logos/decisions/D-2026-0014.json`.
- Cerrado.

### P4 — R-21 (kernel multi-IA): version concisa de D-B
- Estado: PENDIENTE. Se agrega despues de aprobar D-B (ya aprobada).
- Accion: redactar R-21 y agregar a `~/.logos/core/protocol/protocols.json`.
- Referencia: D-2026-0013.

### P5 — R-22 (kernel multi-IA): version concisa de D-C
- Estado: PENDIENTE. Se agrega despues de aprobar D-C (ya aprobada).
- Accion: redactar R-22 y agregar a `~/.logos/core/protocol/protocols.json`.
- Referencia: D-2026-0014.

### P6 — Procedimiento vinculado a D-A
- Estado: PENDIENTE. Metodo detallado de auditoria del Entrenador.
- Accion: definir ubicacion autoritativa (verificar MANIFEST) y redactar.
- Referencia: D-2026-0012, nivel B.6.


### P7 — Reparacion del bug en PROTOCOLO.md
- Estado: CERRADO (commit 0409e8e).
- Seccion "Proteccion de Decisiones Arquitectonicas" ahora incluye
  "Formato obligatorio" completo (8 puntos, validados con Luna).
- Referencia: D-2026-0013 (regla de no-olvido).

### P8 — Limpieza de escapes markdown en PROTOCOLO.md
- Estado: CERRADO (commit 822a4d8).
- Escapes markdown eliminados (124 en total). CRLF -> LF.
  232 lineas tocadas, sin cambio semantico.
- Verificacion: 0 escapes restantes; archivo UTF-8 sin CRLF.

### P9 — R3 "Leer fuentes completas antes de planificar"
- Estado: CERRADO (commit 30c77c6).
- Seccion nueva "Reglas metodologicas obligatorias" en PROTOCOLO.md.
- R3 unica regla de la seccion. R2 y R4 ya tratadas via D-2026-0014
  y D-2026-0013 (sin duplicacion).

---


### P10 — Marcacion visual de outputs por seccion
- Estado: PENDIENTE. Idea del Director, no urgente.
- Idea: que un hilo pueda marcar visualmente las partes de un
  output para copiar solo lo necesario, no todo. Puede ser color,
  separadores, etiquetas, lo que sea que ayude a golpe de vista.
- Nota: si complica cualquier otra cosa, no se implementa.
- Candidatos de aplicacion: logos-foco, logos-gate, cualquier
  comando que devuelva bloques largos.
- A definir: mecanismo, compatibilidad con copia/pegado, si va
  solo en interactivo.
- Sin autoridad asignada todavia. Se retoma cuando logos-foco v1
  este funcionando y haya un caso real que lo justifique.


### P11 — LOGOS v1.1 sin formalizar como D-XXXX
- Estado: PENDIENTE. Reportado por el brief de arranque 2026-10-14.
- Situacion: LOGOS v1.1 (logos-reconcile + drift detection +
  logos-brief) esta implementado en el repo pero no fue
  registrado como D-XXXX en el registro instituido.
- Es el patron exacto que D-2026-0013 resuelve: trabajo hecho
  sin cierre institucional.
- Accion: redactar propuesta D-XXXX para LOGOS v1.1, referenciar
  commits de implementacion, someter a aprobacion del Director.
- Referencia: brief de arranque 2026-10-14, seccion 5.

### P12 — Pendientes del brief de arranque (2026-10-14)
- Estado: PENDIENTE. Items reportados por el brief en su seccion
  7 ("Pendientes priorizados"). Son del proyecto NAVEGO, no del
  hilo cerrado el 2026-10-14.
- Items:
  1. Track honesto — perdida por migracion Doc 46.
  2. Field log no se escribe tras reinicio del celular.
  3. Diseno pendiente: jerarquia de confianza de fuentes para
     cartas nauticas.
  4. Auto-commit WIP en logos-arranque.
  5. Blender MCP — velas dinamicas + timon + mastil no rigido.
- Accion: cada item se atiende por separado, con su propia
  hipotesis o propuesta segun corresponda. Este bloque los
  registra para que no se pierdan al regenerar el brief.
- Referencia: brief de arranque 2026-10-14.

### P13 — Renombrar PENDIENTES_NAVEGO.md a BITACORA_OPERATIVA_NAVEGO.md
- Estado: CERRADO (commit c5fc7e2, 2026-10-14).
- Situacion: el archivo ~/.logos/PENDIENTES_NAVEGO.md NO contenia
  solo pendientes. Era bitacora operativa cronologica con
  pendientes, resueltos, descartes, hitos y bugs. El nombre mentia.
- Resolucion: renombrado a ~/.logos/BITACORA_OPERATIVA_NAVEGO.md.
  Backup: PENDIENTES_NAVEGO.md.pre-rename. logos-brief actualizado
  con fallback entre nombre nuevo y viejo.
- Referencia: consulta a Luna 2026-10-14.

### P14 — Declarar bitacora en MANIFEST como historical no autoritativo
- Estado: CERRADO (commit c5fc7e2, 2026-10-14).
- Situacion: la bitacora aportaba contexto historico, no estado
  vigente. R-18 (source of truth) exigia declarar la autoridad.
- Resolucion: MANIFEST actualizado.
  Bitacora: type historical_bitacora, authority false, role
  historical_log, path ~/.logos/BITACORA_OPERATIVA_NAVEGO.md.
  Nueva source: EXPEDIENTE/PENDIENTES.md, type pending, authority
  true, role singleton. 'pending' movido de optional[] a
  required[].
  Baseline posterior (commit 42ac0bf): 5 fuentes autoritativas
  actualizadas a c5fc7e2.
- Referencia: criterios de Luna (2026-10-14), puntos 5 y 6.

### P15 — Redisenar seccion 7 del brief
- Estado: CERRADO PARCIAL (commit aa360a1, 2026-10-14).
- Situacion: logos-brief seccion 7 leia solo PENDIENTES_NAVEGO.md
  y tomaba los ultimos 5 headers ###. No leia
  EXPEDIENTE/PENDIENTES.md. Resultado: brief desactualizado.
- Resolucion (parte 1): seccion 7 lee EXPEDIENTE/PENDIENTES.md y
  filtra pendientes NO cerrados (excluye APROBADO, CERRADO,
  RECHAZADO, DIFERIDO). Fallback a bitacora historica con aviso
  explicito. Verificado: 22 pendientes activos listados.
- Pendiente (parte 2): regla de integridad completa (P17) y la
  bitacora como contexto historico validado por fecha. Va al hilo
  nuevo.
- Referencia: consulta a Luna 2026-10-14.

### P16 — Agregar seccion "Decisiones recientes" al brief
- Estado: CERRADO (commit ce5afd9, 2026-10-14).
- Situacion: el brief no mostraba las D-XXXX recientes.
  D-2026-0011 a 0014 eran invisibles al arrancar un hilo nuevo.
- Resolucion: nueva seccion 8 "Decisiones recientes". Lee
  .logos/decisions/*.json, filtra estado CONGELADA, ordena por
  (fecha, id) descendente, muestra hasta 7. Renumera secciones
  posteriores (8->9, 9->10, 10->11).
- Verificado: D-2026-0014 a D-2026-0008 visibles en el brief.
- Referencia: criterios de Luna 2026-10-14, punto 4.

### P17 — Regla de integridad en el brief
- Estado: PENDIENTE.
- Situacion: si una fuente falta o esta desactualizada, el brief
  hoy no lo advierte. Presenta la foto del 02 oct como si fuera
  vigente.
- Accion: implementar regla de integridad. Si falta fuente, no se
  puede leer, o esta desactualizada (por ejemplo, ultima
  actualizacion > X dias), el brief debe declararlo explicitamente.
  Nunca presentar como vigente lo que no lo es.
- Referencia: criterios de Luna 2026-10-14, punto 7.

### Nota — hallazgo de fecha desfasada en la bitacora
- Detectado 2026-10-14: ediciones del 08 oct (Auto-commit WIP +
  Blender MCP) quedaron bajo el header "2026-10-02 (cierre de
  jornada)". El diff contra .pre-blender confirma 3 KB de
  contenido agregado sin encabezado nuevo.
- No es pendiente accionable por si mismo. Es evidencia del patron
  que R3 previene (leer fuentes completas, no solo encabezados).
- Al declarar la bitacora como historical (P14), este desfase
  queda como parte del historico. No se corrige.

## PENDIENTES MIGRADOS DE LA BITACORA — 2026-10-14

Los siguientes 11 items fueron detectados en la bitacora
operativa entre el 25 y 26 de septiembre de 2026. Se migran aqui
para que no se pierdan en el renombre de la bitacora (P13) ni en
el rediseno del brief (P15). Todos con estado NO VERIFICADO:
no se afirma que sigan abiertos ni que esten resueltos. Requieren
contraste con codigo, tests y comportamiento actual.

### P18 — [APP] Sesion se guarda sin confirmacion
- Estado: NO VERIFICADO. Origen: 26-09-2026.
- Situacion: al tocar "Finalizar" el Alert es informativo, no
  permite cancelar. La sesion ya se cerro.
- Accion: reproducir el flujo, inspeccionar persistencia/UI y
  revisar tests. Cierre requiere validacion funcional del Director.
- Responsable: IA (verificacion); Director (cierre).

### P19 — [APP] "Referencia ya existe" sin referencia real
- Estado: NO VERIFICADO. Origen: 26-09-2026.
- Situacion: cartel dice que la referencia ya existe pero NO
  aparece en el listado. Mapa no carga en detalle.
- Accion: rastrear la comprobacion de existencia, reproducir el
  caso, revisar tests de persistencia.
- Responsable: IA (verificacion); Director (cierre).

### P20 — [APP] Funcion deshacer (undo)
- Estado: NO VERIFICADO. Origen: 26-09-2026.
- Situacion: deshacer correccion de distancia o punto.
- Accion: contrastar implementacion actual con comportamiento
  esperado, acordar criterio de aceptacion, comprobar tests.
- Responsable: IA + Director.

### P21 — [APP] Borrado de multiples trayectos
- Estado: NO VERIFICADO. Origen: 26-09-2026.
- Situacion: hoy solo se borra un trayecto a la vez.
- Accion: verificar interfaz, seleccion, borrado y persistencia;
  comprobar tests y comportamiento real.
- Responsable: IA + Director.

### P22 — [APP] Logs [FILTER] condicionados a persist
- Estado: NO VERIFICADO. Origen: 26-09-2026.
- Situacion: en POST, [FILTER] se emite dentro de
  persistFixResult con early-return. Regresion observable en logs.
- Accion: inspeccionar las llamadas y determinar mediante tests
  si el registro desaparece cuando no se persiste.
- Responsable: IA.

### P23 — [APP] Doble Date.now() en measuredAt
- Estado: NO VERIFICADO. Origen: 26-09-2026.
- Situacion: callback y persistFixResult calculan Date.now() por
  separado. Si location.timestamp es null/0, difieren.
- Accion: rastrear la generacion de la marca temporal, verificar
  su semantica y revisar tests.
- Responsable: IA.

### P24 — [APP] Posible rechazo no gestionado en void persistFixResult
- Estado: NO VERIFICADO. Origen: 26-09-2026.
- Situacion: el callback hace void persistFixResult(...) sin
  .catch. Puede escalar en RN.
- Accion: seguir el flujo asincrono, inspeccionar el tratamiento
  de errores, verificar el caso de rechazo.
- Responsable: IA.

### P25 — [HIGIENE] Revisar ~/recup_dir.*
- Estado: NO VERIFICADO. Origen: 26-09-2026.
- Situacion: ~1000 carpetas residuo de photorec (13 sep).
  Ensucia find/grep recursivo. NO BORRAR sin inventario previo.
- Accion: identificar origen, contenido, antiguedad y utilidad
  antes de proponer limpieza. Filtro temporal: grep -v recup_dir.
- Responsable: IA + Director.

### P26 — [APP] Gaps chicos < 15 m se suman como observados
- Estado: NO VERIFICADO. Origen: 25-09-2026.
- Situacion: gaps < 15m deberian NO sumar distancia.
- Candidato (pista, no prueba): commit 5251505 subio
  GAP_THRESHOLD_MS a 15000.
- Accion: contrastar comportamiento actual con el commit
  candidato; probar gaps inferiores, iguales y superiores al
  umbral. El commit NO es evidencia de cierre.
- Responsable: IA + Director.

### P27 — [LOGOS] logos-mem: leer hipotesis PROPUESTA y CONFIRMADA
- Estado: NO VERIFICADO. Origen: 25-09-2026.
- Situacion: logos-mem lee solo hipotesis EN_CURSO. Deberia leer
  PROPUESTA y CONFIRMADA.
- Accion: revisar implementacion y tests para ambos estados.
  Comprobar comportamiento actual.
- Responsable: IA (verificacion); Director (cierre).

### P28 — [LOGOS] Test de regresion incidente 20/09 (H-2026-0019)
- Estado: NO VERIFICADO. Origen: 25-09-2026.
- Situacion: test de regresion del incidente multi-escritor.
- Accion: localizar la hipotesis y la evidencia del incidente,
  comprobar si existe el test y verificar su resultado actual.
- Responsable: IA (verificacion); Director (cierre).

### Reconciliacion de commits
- 29e6f60 (Track honesto) y 6b46436 (Doc 46 Fase 2) se vinculan
  al pendiente institucional "track honesto", NO a P18-P28.
- Los mensajes de commit son pistas, no evidencia de cierre.
### P29 — [LOGOS] logos-baseline y logos-reconcile no actualizan hash
- Estado: CERRADO (commits 7eb1ee1 + 490cc98, 2026-10-14).
- Situacion: ninguna herramienta escribia reviewed_against_hash.
  Fuente modificada quedaba STALE permanentemente hasta fix manual.
  4 fixes manuales durante el hilo (dd5a4b2, fecbe01, 2e03318,
  eb5a24a).
- Resolucion: extraccion de la logica de hashing a
  .logos/lib/logos_hash_lib.py (143 lineas). Los tres binarios
  (logos-hash, logos-baseline, logos-reconcile) importan de ahi.
  - logos-hash: 148 -> 55 lineas.
  - logos-baseline: 147 -> 181 lineas. Calcula y escribe hash.
    baseline_history incluye hash por fuente. last_human_review NO
    se actualiza (criterio de Luna).
  - logos-reconcile: 356 -> 376 lineas. Escribe hash. 'nada que
    escribir' solo si commit Y hash coinciden. Dry-run muestra
    diff de hash.
- Tests: paridad exacta de logos-hash antes/despues sobre 5
  fuentes; 4 tests de regresion (mismo commit+hash, commit
  distinto, hash distinto, fuente inexistente).
- Pendiente separado: P30 (symlink a directorio), P31 (errores de
  lectura silenciosos) - P31 se corrigio en este mismo fix
  (la lib propaga errores en vez de saltearlos).
- Referencia: D-2026-0009, D-2026-0010, D-2026-0015 (borrador).
- Decision formal: D-2026-0015 (CONGELADA).

### P30 — [LOGOS] Symlink a directorio se pierde en hash_directory_standard
- Estado: PENDIENTE. Detectado: 2026-10-14 durante analisis P29.
- Situacion: en logos-hash, hash_directory_standard usa os.walk
  con followlinks=False (default). Los symlinks a directorio NO se
  recorren, pero tampoco se registran como metadata. Se pierden
  silenciosamente del hash. Los symlinks a archivo SI se registran
  como LINK:<target>. Inconsistencia.
- Alcance: no se corrige en D-0015/P29 (esa mantiene equivalencia
  exacta con comportamiento actual). Requiere decision propia.
- Accion: disenar semantica. Opcion propuesta por Luna: registrar
  el enlace como metadata LINK:<target> sin recorrer destino.
  Anadir test de symlink a directorio que documente la omision
  actual como referencia.
- Referencia: analisis 2026-10-14, consulta a Luna.
- Responsable: IA + Director (aprobacion).

### P31 — [LOGOS] Errores de lectura se tragan silenciosamente en hashers
- Estado: CERRADO (commits 7eb1ee1 + 490cc98, 2026-10-14).
- Resolucion: corregido dentro del fix P29. La biblioteca compartida
  .logos/lib/logos_hash_lib.py PROPAGA errores de lectura en vez de
  saltearlos silenciosamente. Los consumidores bloquean ante HashError.
  Semantica previa (inaceptable): except (OSError, PermissionError):
  continue. Semantica nueva: la excepcion sube, el consumidor decide.
- Situacion: en hash_directory_standard y hash_directory_git de
  logos-hash, los bloques:
      except (OSError, PermissionError):
          continue
  saltean archivos ilegibles sin avisar. El hash resultante cambia
  respecto al esperado, pero nadie lo detecta.
- Alcance: DEBE corregirse en la D-0015 (parte del fix P29). La
  biblioteca compartida debe PROPAGAR los errores de lectura que
  impidan calcular un hash integro. Un hash silenciosamente
  incompleto es peor que un fallo visible.
- Accion: en logos_hash_lib.py, cualquier error de lectura que
  impida hashear un archivo lanza excepcion. Los consumidores
  bloquean ante ella (aplica el criterio 'falla segura').
  Tests: fuente con archivo ilegible -> BLOCKED sin escrituras
  parciales.
- Referencia: analisis 2026-10-14, consulta a Luna.
- Responsable: IA + Director (aprobacion).

### P32 — [LOGOS] Unificar hashing de logos-gate y detectar errores de recorrido
- Estado: CERRADO (2026-10-14). Commit de implementacion: `e72a6e3`.
- Resultado: `logos-gate` delega el hashing en `logos_hash_lib.py`. Los fallos de inspeccion, lectura, recorrido o ejecucion Git se propagan como `HashError`; el Gate clasifica los errores como `INVALID`, bloquea fuentes requeridas y advierte para las opcionales.
- Evidencia reproducible: `.logos/tests/test_p32_hashing.py`; 16 pruebas pasaron despues del commit (`TEST_EXIT=0`). Compilacion (`PY_COMPILE=0`) y `git diff --check` (`DIFF_CHECK=0`) tambien pasaron.
- Validaciones de integracion: fuente requerida con error -> `INVALID/BLOCKED`, codigo 2; fuente opcional con error -> `INVALID/WARNING`, codigo 1. Las pruebas de `logos-baseline` y `logos-reconcile` demostraron que un error de hashing no modifica el MANIFEST. El reemplazo atomico de `logos-reconcile` preserva el archivo anterior ante fallo simulado y limpia el temporal.
- Correcciones verificadas: se distingue archivo Git realmente eliminado de error de acceso; `hash_source()` distingue ruta realmente inexistente de error de inspeccion. Se comprobo paridad en casos de archivo, directorio, symlink, repo Git y archivo eliminado.
- Alcance excluido: P30 sigue separada; la correccion funcional de symlinks a directorios no forma parte de P32.
- Limite documentado: `logos-baseline` se comprobo ante fallos durante el calculo de hashes, no ante un fallo durante su escritura final directa. Esa mejora de atomicidad queda fuera de P32.
- Referencia: D-2026-0016, D-2026-0015, P30 y antecedentes de P31.
- Responsable: IA (implementacion y pruebas); Director (autorizacion de cierre).

### P33 — [NAVEGO] Validar y registrar memo técnico Polaris–Timonel (2026-10-15)
- Estado: APROBADO (2026-10-15, Director). Memo validado e incorporado al expediente.
- Fuente: timonel/borradores/MEMO_TECNICO_NAVEGO_POLARIS_TIMONEL_2026-10-15.md
- SHA-256 de la fuente: 19a5f2b7ded04f59556e86c9bf7697a2f5a47bce395bee4bfa80680aa7a19e86
- Objetivo: contrastar las observaciones de Polaris, la telemetría, el controlador activo y la participación del LLM con la evidencia disponible y los memos 89 y 90.
- Acción: realizar revisión técnica cruzada, documentar discrepancias y límites de evidencia, y proponer si corresponde promover el memo al expediente como documento nuevo y enlazarlo desde el mapa de arquitectura.
- Criterio de aceptación: revisión documentada, hash de la fuente preservado y resolución expresa del Director sobre el estado del pendiente.
- Responsable: IA prepara el contraste; el Director decide APROBADO, RECHAZADO o DIFERIDO.

### P34 — [SIM] Divergencia de física Python vs Godot
- Estado: PENDIENTE. Detectado 2026-10-15.
- Fuente: timonel/borradores/divergencia_fisica_python_godot_2026-10-15.md
- Situación: dos implementaciones de física coexisten (Python: 12 probes, drag lateral 0.05; Godot: 168 puntos de malla, drag lateral 1.20). Timonel entrena contra Python pero opera contra Godot. El drag angular diverge ×70.
- Objetivo: declarar modelo canónico, diseñar mecanismo de paridad, agregar campo `modelo_fisico` al contrato de datos.
- Acción: revisar divergencia completa, aprobar declaración de modelo canónico, diseñar test de paridad.
- Criterio de aceptación: campo `modelo_fisico` obligatorio en contrato de datos + test de paridad documentado.
- Responsable: IA prepara propuesta; Director decide APROBADO/RECHAZADO/DIFERIDO.

### P35 — [SIM] Paridad activa entre simuladores Python y Godot
- Estado: PENDIENTE. Detectado 2026-10-15 (derivado de P34).
- Fuente: timonel/borradores/divergencia_fisica_python_godot_2026-10-15.md
- Situación: Python y Godot implementan la misma física con parámetros distintos (12 vs 168 puntos de flotabilidad; drag lateral 0.05 vs 1.20; drag angular 0.005 vs 0.35). No hay mecanismo que detecte cuándo divergen.
- Objetivo: (1) fuente única de parámetros físicos en JSON compartido; (2) test de paridad activo que corra el mismo input en ambos simuladores y reporte OK/WARNING/INCOMPATIBLE; (3) check de integridad en el arranque de cada corrida.
- Política de severidad: WARNING por defecto. INCOMPATIBLE solo cuando la divergencia invalida específicamente la variable que la corrida quiere medir. No bloquear por defecto — las diferencias pueden ser experimentales.
- Acción: diseñar el contrato de parámetros compartidos, el test de paridad y el check de arranque. Sin implementación hasta aprobación del Director.
- Criterio de aceptación: los tres mecanismos definidos y validados con al menos una corrida comparada entre ambos simuladores.
- Regla de aislamiento (agregada 2026-10-15 tras Experimento 0): el runner headless y todo test automatizado deben escribir en carpeta aislada por corrida (`~/.logos/runs/<run_id>/` o equivalente). Prohibido sobreescribir archivos de sesión activa. Verificado empíricamente: un test headless dejó `timonel/telemetria.jsonl` en 0 bytes.
- Precondición: el runner headless de Godot es habilitador del test de paridad. Sin runner automatizable, la paridad no se puede verificar de forma continua.
- Responsable: IA prepara propuesta; Director decide APROBADO/RECHAZADO/DIFERIDO.

### P36 — [SIM] Velas en simulador Python
- Estado: PENDIENTE. Detectado 2026-10-15 tras contraste de cobertura.
- Fuente: timonel/borradores/contraste_cobertura_python_godot_2026-10-15.md
- Situación: Godot tiene velas (Vela_Mayor, Foque) que modulan el viento según ángulo. Python aplica viento pleno sin modelar velas. No es impedimento técnico — es alcance postergado.
- Objetivo: implementar `vela_mayor_deg` y `vela_foque_deg` en `Barco`, con la misma fórmula que `wind.gd:69-74`. Habilita la Fase 2 del curriculum (uso de velas) en Python.
- Acción: diseñar los campos, aplicar la fórmula de efectividad por ángulo, agregar torque de yaw por diferencia de empuje proa/popa, prueba de humo.
- Criterio de aceptación: barco con velas a 0° no recibe empuje de viento; velas perpendiculares al viento reciben empuje máximo; el controlador puede moverlas.
- Responsable: IA implementa; Director aprueba cierre.

### P37 — [DOC] Referencia externa Beneteau First Class 8
- Estado: PENDIENTE. Detectado 2026-10-15 (recomendación de Luna).
- Referencia: "A Hardware-in-the-Loop Simulator to Optimize Autonomous Sailboat Performance in Real Ocean Conditions" (MDPI, 2023).
- URL: https://www.mdpi.com/2077-1312/11/6/1104
- Objetivo: verificar si el paper publica ecuaciones, coeficientes, ensayos de tanque y registros de navegación recuperables para anclar la física de Polaris en evidencia externa.
- Acción: descargar el paper, inspeccionar secciones de modelo físico y validación, registrar qué es reutilizable y qué es específico del Beneteau.
- Criterio de aceptación: ficha del paper con secciones de modelo, validación y aplicabilidad. Si los datos no son recuperables, declararlo y cerrar sin extender la búsqueda.
- Responsable: IA analiza; Director decide si la referencia se incorpora.

### P38 — [E1] Actualizar contraste de cobertura con decisiones de modelo canónico
- Estado: PENDIENTE. Detectado 2026-10-15.
- Fuente: timonel/borradores/contraste_cobertura_python_godot_2026-10-15.md
- Situación: la tabla de cobertura muestra que Python y Godot representan fenómenos distintos. Antes de elegir un modelo para cada pregunta experimental, la tabla queda como referencia.
- Acción: cuando se decida qué modelo usar para cada comparación (velas, roll, prop_walk, casco), actualizar la tabla con la decisión y su justificación.
- Criterio de aceptación: tabla con columna adicional "modelo elegido" por fila.
- Responsable: IA propone; Director decide.

## REGLAS DE ESTE REGISTRO

1. Un pendiente no se cierra por silencio ni por paso de tiempo.
2. Solo el Director marca APROBADO, RECHAZADO o DIFERIDO.
3. DIFERIDO requiere motivo y condicion de revision explicitos.
4. La IA puede agregar pendientes; no puede cerrarlos.
5. Referencia cruzada obligatoria con la D o el memo de origen.
