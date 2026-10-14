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
- Estado: PENDIENTE. Detectado: 2026-10-14 durante migracion authority.
- Situacion: ninguna herramienta escribe reviewed_against_hash en
  el MANIFEST. logos-baseline y logos-reconcile actualizan solo
  reviewed_against_commit. logos-hash calcula pero no escribe.
  Consecuencia: una fuente modificada queda STALE permanentemente
  hasta editar el MANIFEST a mano.
- Evidencia: gate BLOCKED tras commit d48543f. Comandos baseline y
  reconcile aplicados. Hash en MANIFEST quedaba en 01225fa7...
  mientras el real era 44be285e...
- Accion: aplicar R-15 (pasar por expediente antes de tocar el
  kernel). Redactar D-XXXX o propuesta. Corregir logos-baseline y
  logos-reconcile para actualizar hash. Anadir tests.
- Referencia: D-2026-0009 (estados de drift), D-2026-0010 (freshness
  por hash), commit dd5a4b2 (fix manual).
- Responsable: IA + Director (aprobacion).

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
- Estado: PENDIENTE. Detectado: 2026-10-14 durante analisis P29.
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

## REGLAS DE ESTE REGISTRO

1. Un pendiente no se cierra por silencio ni por paso de tiempo.
2. Solo el Director marca APROBADO, RECHAZADO o DIFERIDO.
3. DIFERIDO requiere motivo y condicion de revision explicitos.
4. La IA puede agregar pendientes; no puede cerrarlos.
5. Referencia cruzada obligatoria con la D o el memo de origen.
