# Bitácora de activos, salud y avalúo — LOGOS / NAVEGO

**Versión:** 0.3 — corrección de evidencia de campo y separación de madurez operativa/formalización
**Fecha de corte:** 2026-10-22
**Estado:** propuesta de trabajo; no es norma aprobada ni auditoría concluida.
**Autoridad:** Iván, Director Ejecutivo. La IA releva, organiza y propone; el Director corrige y decide.

---

## Hallazgo principal

**NaveGo es el activo con mayor madurez operativa (O3, evidencia de campo documentada en `EXPEDIENTE/50` y `ANALISIS_TCL_FIELD_01.md`) y el de menor formalización end-to-end (F3, sin test único que reproduzca el viaje completo).**

**GNSS es el subsistema más formalizado (F4)**: 8 tests, `exp_dist/2/3`, bitácora de cierre con `sha256_resultados.txt`.

**LOGOS kernel está en O4/F4** pero solo cubre gobernanza, no producto.

**Simulador/Polaris tiene evidencia real (O3/F4)**: misión Puerto Esperanza hardcodeada en `timonel/timonel.py:181` (36, -6); 4 corridas con `ground_truth.jsonl` en `~/.logos/runs/`; 18 corridas con resúmenes en `timonel/corridas/` (2026-10-04); telemetría en `pruebas_dsh/`; 13 experimentos indexados en `EXPEDIENTE/96`; informe consolidado en `EXPEDIENTE/95`. No es solo "declaración del Director".

**El bache sin costura:** el puente entre campo (viajes, corridas) y código (tests que vinculen viaje ↔ versión ↔ criterio) es parcial. GNSS lo tiene; NaveGo app no lo tiene end-to-end; Timonel tiene datasets y corridas pero tests mezclados con scripts.

---

## 0. Decisión de diseño

Tres fases analíticas, dos iteraciones operativas, una sola bitácora. La valoración sale del inventario y de la revisión de salud.

- **Fase 1 — Inventario:** activos, función, estado, evidencia, dependencias.
- **Fase 2 — Salud:** semáforo por dimensiones con justificación de una línea.
- **Fase 3 — Avalúo:** perfil de valor, costo de reposición, riesgos, opciones.

**Iteración 1:** cerrar inventario preliminar y corregirlo con el Director (esta versión).
**Iteración 2:** contrastar fuentes, completar semáforo y derivar valoración por rangos.

---

## 1. Principios

1. **Registrar una vez:** fuente canónica, referencias desde otros lugares.
2. **Automatizar lo repetitivo:** controles reproducibles donde sean seguros.
3. **Documentar según utilidad:** si permite decidir, reconstruir, reducir riesgo o evitar error.
4. **Automatización ≠ autoridad:** la IA prepara y valida; no aprueba por silencio.
5. **Cada incidente simplifica el sistema** al resolverse.
6. **El tiempo del Director es parte del sistema.**
7. **Integridad ≠ veracidad:** SHA-256 verifica coincidencia, no verdad.
8. **No inflar ni descartar por falta de localización inmediata.**

---

## 2. Etiquetas

### 2.1 Estado de evidencia

| Código | Significado |
|---|---|
| **D** | Declaración identificada |
| **R** | Registro o artefacto identificable (commit, archivo, log, test, backup, captura) |
| **I** | Inspeccionado directamente |
| **V** | Verificado mediante procedimiento descrito y criterio previo |
| **C** | Corroborado por fuentes independientes |
| **H** | Hipótesis por comprobar |
| **X** | Refutado bajo condiciones explícitas |

### 2.2 Madurez en dos ejes (O/F)

**Eje operativo (O):**
- O0 — declarado
- O1 — componente probado (banco)
- O2 — comportamiento controlado
- O3 — demostrado en campo real documentado
- O4 — campo repetido con registros comparables
- O5 — operación mantenible con recuperación y regresión vinculada a versión

**Eje formalización/reproducibilidad (F):**
- F0 — sin artefacto
- F1 — documentación localizada
- F2 — registro estructurado con procedencia
- F3 — procedimiento de prueba reproducible con criterios
- F4 — pruebas automatizadas repetibles
- F5 — regresión automatizada ligada a versión/release end-to-end

Escalas internas, no TRL/ISO/CMMI/COBIT oficiales.

### 2.3 Imparcialidad

La fuente primaria depende de la pregunta: Iván/operador para campo; código para implementación; logs/datos para eventos; pruebas reproducibles para comportamiento; proveedores para especificaciones; fuentes oficiales para estándares.

Una IA que propuso una teoría no cuenta como revisora independiente. En cuestiones críticas, comprobación independiente o prueba que refute.

---

## 3. Inventario

### 3.1 Vista ejecutiva (7 pilotos)

| ID | Activo | O | F | Evidencia principal |
|---|---|---|---|---|
| A-01 | NaveGo app | O3 | F3 | logs/viaje_*, regression_2026-09-27/30, db_export, test_fase2 |
| A-03 | GNSS 2do plano | O3 | F4 | 8 tests GNSS, exp_dist/2/3, bitácora 21-10 sha256 |
| A-04 | Track Honesto | O2 | F2 | CT-01, EXPEDIENTE/50 (bug 6%), exp_gaps_avance, exp_ruido_vs_gap |
| A-07 | LOGOS kernel | O4 | F4 | Gate READY 22-10, trust, 5 tests logos |
| A-09 | Timonel | O3 | F3 | simulador_polaris.py+11 backups, timonel/corridas/ (18), EXPEDIENTE/96 (13 experimentos), EXPEDIENTE/95 |
| A-10 | Simulador/Polaris | O3 | F4 | timonel.py:181 (Puerto Esperanza 36,-6), ~/.logos/runs/ (4 ground_truth), timonel/corridas/ (18), EXPEDIENTE/96 (13 experimentos), EXPEDIENTE/95 |
| A-15 | Infraestructura | O4 | F3 | Git remoto, build_release_*.log, backups |

### 3.2 Tabla completa (18 activos)

| ID | Activo | O | F | Evidencia | Notas |
|---|---|---|---|---|---|
| A-01 | NaveGo app | O3 | F3 | logs/viaje_* (ida+vuelta+sha256), regression_2026-09-27/, regression_2026-09-30_BASE.log, db_export_2026-09-30/, test_fase2_2026-09-30/ | Sin test E2E único |
| A-02 | HUD (SOG/COG/dist) | O3 | F2 | Incluido en A-01 | Sin test específico |
| A-03 | GNSS 2do plano | O3 | F4 | 8 tests GNSS, exp_dist/2/3, bitácora cierre 21-10 con sha256_resultados.txt, ANALISIS_TCL_FIELD_01.md | El más formalizado |
| A-04 | Track Honesto | O2 | F2 | CT-01, EXPEDIENTE/50 (bug 6%), exp_gaps_avance, exp_ruido_vs_gap | Pendiente criterio cierre |
| A-05 | Cartografía | O2 | F2 | En A-01 | Sin test offline por función |
| A-06 | Guardado/export | O1 | F1 | Sin test específico localizado | Antecedente de fallo |
| A-07 | LOGOS kernel | O4 | F4 | Gate READY 22-10, trust, 5 tests logos | Checkpoint, no auditoría completa |
| A-08 | Gobernanza | O3 | F3 | Commits, PENDIENTES.md, 03_WORKFLOW.md reconciliado | P43 obsoleto, mark-reviewed pendiente |
| A-09 | Timonel | O3 | F3 | simulador_polaris.py+11 backups, agente_llm.py+13 backups, sft_dataset/, banco_cc002/cc003, lora_*, kaggle_*, pruebas_dsh/, timonel/corridas/ (18 corridas 04-10), timonel.py con MISION; EXPEDIENTE/96 (13 experimentos oct), EXPEDIENTE/95 | Tests mezclados con scripts (1/6 con assert); memo 96 declara falta de metadata/hash por experimento |
| A-10 | Simulador/Polaris | O3 | F4 | Mision hardcodeada en timonel/timonel.py:181 (Puerto Esperanza en 36,-6); ~/.logos/runs/ (4 corridas con ground_truth.jsonl); timonel/corridas/ (18 corridas 2026-10-04); pruebas_dsh/20261015_123336/; EXPEDIENTE/96 (memo indice 13 experimentos oct); EXPEDIENTE/95 (informe consolidado 21-10); memo 15-10 | Evidencia distribuida, no consolidada en un solo lugar. Memo 96 declara falta de metadata/hash por experimento |
| A-11 | Taller multi-IA | O2 | F2 | 09_PROTOCOLO_MULTI_IA.md, agente_llm.py | Interfaz no inspeccionada |
| A-12 | Datos GNSS | O3 | F4 | docs/gnss/v2/gtgen/, obsgen/, ground_truth_*.jsonl | Calidad varía por dataset |
| A-13 | Estudios distancia | O3 | F3 | exp_dist/2/3, exp_gaps_avance, exp_ruido_vs_gap, HALLAZGOS_FASE_A_v1.md | Algunas conclusiones en pausa |
| A-14 | Commodities | - | - | Pendiente iteración 2 | No atribuir como propio |
| A-15 | Infraestructura | O4 | F3 | Git remoto, build_release_*.log, backups | Restauración no probada |
| A-16 | Know-how | O3 | F2 | Expedientes 00-99, commits, CT-01 | Recuperabilidad parcial |
| A-17 | Ojo de Gaia | O1 | F1 | Por verificar iteración 2 | Proyecto incipiente |
| A-18 | Automatización push | O0 | F0 | Deshabilitado por decisión | Opción futura |

### 3.3 Reglas de completado

- Una fila por activo o subsistema con utilidad diferenciada.
- Cada fila con una evidencia principal; complementarias en nota.
- **Regla de 5 minutos:** si en una búsqueda dirigida de ≤5 minutos no aparece la evidencia, se marca `SIN EVIDENCIA LOCALIZADA EN ESTA PASADA` y se sigue con la siguiente fila. No se abre investigación por celda. La ausencia de localización no equivale a inexistencia.
- No tocar los ~1500 archivos untracked bajo `docs/gnss/v2/obsgen/fixes/` durante esta auditoría.

---

## 4. Salud (semáforo)

| Dimensión | Controles | Señal inicial |
|---|---|---|
| Calidad del producto | funciones críticas ligadas a versión; prueba reproducible; fallos visibles | AMARILLO: campo+regresión existen; ciclo sesión/track con incidente; guardar/exportar sin confirmar |
| Madurez del proceso | cambios reproducibles; respaldo/restauración; tests repetibles | AMARILLO: commits, respaldos, Gate; fricción reciente |
| Gobernanza TI | decisiones explícitas; sello vigente; pendientes reales | AMARILLO global / VERDE checkpoint Gate |
| Deuda técnica | fallos priorizados; huérfanos clasificados; docs sin drift | AMARILLO: Track Honesto, P43, ~1500 untracked |
| Trazabilidad | commit↔cambio↔decisión↔prueba; real vs sintético; hashes | VERDE resellado 22-10 / AMARILLO historia total |

**Semáforo global: AMARILLO** — evidencia suficiente para no ser gris, insuficiente para verde por brechas de formalización en A-04/A-06/A-17.

## 5. Avalúo

### 5.1 Perfil de valor

| Componente | Qué estima | Regla de honestidad |
|---|---|---|
| Servicio interno | Capacidad, tiempo evitado, dependencias | Describir beneficio; no atribuir dinero sin cuenta defendible |
| Costo de reposición | Esfuerzo para reconstruir equivalente hoy | Intervalo, alcance, supuestos; separar horas Director/técnicas/IA/gastos |
| Valor de evidencia | Fuerza de las afirmaciones sobre el activo | Factor de confianza, no dinero sumable |
| Mercado/transferencia | Comparables o acuerdos | SIN EVIDENCIA si no hay comparables |
| Opción futura | Oportunidades | Cualitativo mientras falten datos |
| Costo de sostén y riesgo | Mantenimiento, dependencias, obsolescencia, seguridad, recuperación | Riesgo a descontar o gestionar |

### 5.2 Estimación de reposición

Registrar por separado: horas activas de Iván; horas de desarrollador humano; uso de IA medible; herramientas, servicios, hardware, gastos directos; intervalo de incertidumbre, fecha, supuestos.

**No aplicar COCOMO ni puntos de función como generadores automáticos en esta primera pasada.**

### 5.3 Regla de inclusión

- Activo sin evidencia localizada: valor monetario `NO ASIGNADO` (no $0).
- Activo con evidencia solo declarativa: utilidad descrita, no agregar cifra al total confirmado.
- Activo con artefacto identificado: esfuerzo de reposición con confianza baja.
- Activo reproducido con alcance conocido: intervalo y nivel de confianza.
- No sumar horas, valor estratégico, probabilidad y precios de mercado en un total único.

---

## 6. Deuda conocida

- **P43:** descripción dice "trust ausente", obsoleta. Trust existe y sincroniza. Diferido. Antes de cerrar, ejecutar `mark-reviewed` y registrar salida.
- **~1500 untracked** en `docs/gnss/v2/obsgen/fixes/`. No borrar ni añadir en bloque.
- **Informe de distancia:** `EXPEDIENTE/51`, `EXPEDIENTE/94`, `docs/gnss/exp_dist/INFORME_DISTANCIA.md` en pausa/revisión.
- **Push automático:** no activado por decisión.
- **A-06 (guardado/export):** sin test específico.
- **A-17 (Ojo de Gaia):** sin inventario.
- **A-09 (Timonel):** 1/6 tests con assert; el resto son scripts de experimento.
- **A-10 (Simulador/Polaris):** evidencia distribuida en `timonel/`, `~/.logos/runs/`, `EXPEDIENTE/95-96`, `timonel/corridas/`. Consolidar en un lugar canónico y declarar hash de experimento queda para iteración 2.

---

## 7. Plan de dos iteraciones

### Iteración 1 (esta versión)
- Inventario corregido con evidencia real (hecho).
- Tabla de 7 pilotos verificada (hecho).
- Deuda conocida listada (hecho).

### Iteración 2
- Contrastar `~/.logos/runs/*/ground_truth.jsonl` con versión de simulador y resultado de Puerto Esperanza.
- Verificar `timonel/corridas/` (contenido no inspeccionado).
- Ejecutar `mark-reviewed` y registrar salida (P43).
- Verificar A-06 (guardar/exportar) contra versión actual.
- Inventariar A-17 (Ojo de Gaia).
- Clasificar `~/.logos/runs/` (¿son las corridas a Puerto Esperanza?).
- Actualizar semáforo con datos de iteración 2.

---

## 8. Decisiones no adoptadas

Esta versión no crea ni modifica archivos dentro de `~/navego_recuperado` salvo este mismo documento; no actualiza el MANIFEST, no toca la raíz de confianza, no cierra P43, no aprueba norma, no asigna certificación oficial ni afirma valor contable o precio de venta.

---

## 9. Referencias metodológicas (marcos adaptados, no certificaciones)

- **OCDE — Manual de Frascati:** criterios para clasificar I+D.
- **ISO/IEC 25010:2023:** modelo de calidad de producto de software.
- **NASA — System Engineering Handbook / TRL:** madurez según lo demostrado.
- **WIPO — IP Valuation Basics (2025):** métodos de costo, mercado e ingresos/opciones.
- **NIST AI RMF 1.0 Core:** ciclo gobernar → mapear → medir → gestionar.
- **IFRS IAS 38:** distinción entre avalúo interno y reconocimiento contable formal.

No se propone implantar CMMI o COBIT completos.

---

## Anexo A — Declaración fundacional literal del Director

**Procedencia:** mensaje de Iván en el hilo del 22-10-2026. Se conserva la redacción original, con giros y errores tipográficos, para no reemplazar la voz del Director por paráfrasis.

> me gustaría que hagamos los pasos metodológicos y analíticos de una auto auditoría general para comprobar la salud, la dinámica general y cómo y cuáles son los mecanismos más honestos y equilibrados para tener una veheduría justa. Contemplando tiempo de todo lo que se hizo desde su inicio. Tanto para Navego que comenzó a existir como desarrollo de una aplicación y Luego surgió la necesidad de desarrollar Logos para que el sistema tuviera orden y organización más allá de los proyectos que se ejecuten. Pero estamos hablando de aproximadamente 3 meses desde sus inicios en windows todavía. Y ahora tenemos un sistema que va de a poco autoconociéndose. Con varios proyectos con un desarrollo incipiente, con comoditys ya instalados, con un know house ya funcional y con taller de investigación propio(con interfaz usuario/pc/i.a's). Con simuladores reales y sintéticos en interfaz. más allá de todo lo que se ubique en una zona de constante testeo para validar cada una de sus instancias. Pero también con un sistema que tiene un método como filosofía que lo hace único en su operatividad que también es científica en su método poperiano de validación y búsqueda constante de evidencias para ser falseada u evidencia actual. Nacida y concebida con sistema de encriptado y de seguimiento para tener una auditoría y trazabilidad chequeables y auditables (sha 256). Con ya un compendio de desarrollos implementados sistema de hud de navegación con sog, cog, distancia y varias utilidades más, en la app con track de grabado y seguimiento, con mapas que se integran a un sistema de código abierto. funcionando todo offline. Con varios visores independientes portrait, landscape de seguimiento rotativo. Guardado de trayectos en mapa con los waypoint, que pueden superponerse a el mapa en curso real vigente en diferentes colores. Funcionando en segundo plano o a prueba de cierres hasta que el usuario decide conscientemente cerrar la sesión. Testeo múltiples con viajes de 560 kms sin cierre, ni pérdida de gnss en todo el trayecto. El simulador tiene un bridge testeado que múltiples veces fue comandado con perfecto posicionamiento con el Timonel. Fue testeado múltiples veces llevando el Velero Polaris, del simulador desde distancias de más de 500 mts hasta el punto de llegada (Puerto Esperanza). Más un sinnúmero de experimentos trazables y chequeables. Y una interfaz con todas las I.A's con conexión via internet del mercado. Con repositorio de backup en Githube. con todo para implementar push automatizados, que por desición del Director todavía no se implementa. Con la honestidad del dato, de la evidencia por sobre el relato y con la honestidad de decir siempre lo que se registra y lo que no. Y un sin fin de microdesarrollos que algunos serán tan importantes como lo antes mecionado. Así que esto es no sólo para justipreciar la auditoría con sus pros y contras, flaquezas y fortalezas, presente y potencial. Sino que también nos sirva para avaluar, no solo evaluar, sino avaluar, ponerle un "precio" para nosotros, para que nosotros sepamos que herramienta tenemos y como podríamos mensurarlo. Cuál es la escalabilidad y cómo consideramos la arquitectura de Logos y su constelación en general. Cada palabra que digo debe quedar asentada y tenemos que tener un nuevo espacio que es la contabilidad de los activos que consideramos activos y cómo lo mensuramos según los canones actuales en desarrollo de I +D o recomiéndenme el formato de cómo se audita y contabilizan estos vienes y servicios o desarrollos, cuáles activos tenemos implementados y no lo estamos viendo. Armemos una bitácora para que no se nos haga ahora pesado el arranque.. no quiero más de una o dos iteraciones para arrancar.

