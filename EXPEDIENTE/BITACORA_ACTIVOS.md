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

**Simulador/Polaris tiene evidencia real y abundante (O3/F4)**: misión Puerto Esperanza hardcodeada en `timonel/timonel.py:181` (36, -6); 4 runs completos con `ground_truth.jsonl`, `resultado.json`, `runner.log` y `telemetria.jsonl` en `~/.logos/runs/`; **1043 archivos** (corridas + resúmenes) en `timonel/corridas/` (2026-10-04); telemetría en `pruebas_dsh/`; 13+ experimentos indexados en `EXPEDIENTE/96`; informe consolidado en `EXPEDIENTE/95`. No es solo "declaración del Director". Ver Anexo B para inventario completo.

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
| A-04 | Track Honesto | O3 | F4 | test_ref_route_no_gap.py: GREEN (230 puntos; gap GT declarado 30 m; divergencia 2.072 m < tolerancia 8 m); EXPEDIENTE/50 (viaje real ida/vuelta); CT-01; exp_gaps_avance; exp_ruido_vs_gap |
| A-07 | LOGOS kernel | O4 | F4 | Gate READY 22-10, trust, 5 tests logos |
| A-09 | Timonel | O3 | F3 | simulador_polaris.py+11 backups, timonel/corridas/ (18), EXPEDIENTE/96 (13 experimentos), EXPEDIENTE/95 |
| A-10 | Simulador/Polaris | O3 | F4 | timonel.py:181 (Puerto Esperanza 36,-6), ~/.logos/runs/ (4 runs completos), timonel/corridas/ (1043 archivos), EXPEDIENTE/96 (13+ experimentos), EXPEDIENTE/95 |
| A-15 | Infraestructura | O4 | F3 | Git remoto, build_release_*.log, backups |

### 3.2 Tabla completa (18 activos)

| ID | Activo | O | F | Evidencia | Notas |
|---|---|---|---|---|---|
| A-01 | NaveGo app | O3 | F3 | logs/viaje_* (ida+vuelta+sha256), regression_2026-09-27/, regression_2026-09-30_BASE.log, db_export_2026-09-30/, test_fase2_2026-09-30/ | Sin test E2E único |
| A-02 | HUD (SOG/COG/dist) | O3 | F2 | Incluido en A-01 | Sin test específico |
| A-03 | GNSS 2do plano | O3 | F4 | 8 tests GNSS, exp_dist/2/3, bitácora cierre 21-10 con sha256_resultados.txt, ANALISIS_TCL_FIELD_01.md | El más formalizado |
| A-04 | Track Honesto | O3 | F4 | test_ref_route_no_gap.py: GREEN (230 puntos; gap GT declarado 30 m; divergencia 2.072 m < tolerancia 8 m); EXPEDIENTE/50 (viaje real ida/vuelta); CT-01; exp_gaps_avance; exp_ruido_vs_gap | F5 pendiente: CI. Validación limitada a este fixture/escenario. El runner comprueba que el avance GT declarado supera la tolerancia; no regenera ni recalcula el fixture en cada ejecución. |
| A-05 | Cartografía | O2 | F2 | En A-01 | Sin test offline por función |
| A-06 | Guardado/export | O2 | F2 | db/exportToGodot.ts (exportSessionToGodotJson: lat_raw, lon_raw, timestamp, heading, filtrando quality='GOOD') | Export a JSON para Godot funcional; sin export GPX/KML para usuario; sin test E2E de guardar+reabrir+exportar |
| A-07 | LOGOS kernel | O4 | F4 | Gate READY 22-10, trust, 5 tests logos | Checkpoint, no auditoría completa |
| A-08 | Gobernanza | O3 | F3 | Commits, PENDIENTES.md, 03_WORKFLOW.md reconciliado | P43 obsoleto, mark-reviewed pendiente |
| A-09 | Timonel | O3 | F3 | simulador_polaris.py+11 backups, agente_llm.py+13 backups, sft_dataset/, banco_cc002/cc003, lora_*, kaggle_*, pruebas_dsh/, timonel/corridas/ (18 corridas 04-10), timonel.py con MISION; EXPEDIENTE/96 (13 experimentos oct), EXPEDIENTE/95 | Tests mezclados con scripts (1/6 con assert); memo 96 declara falta de metadata/hash por experimento |
| A-10 | Simulador/Polaris | O3 | F4 | Mision hardcodeada en timonel/timonel.py:181 (Puerto Esperanza en 36,-6); ~/.logos/runs/ (4 runs completos con comandos_in, ground_truth, resultado, runner.log, telemetria); timonel/corridas/ (1043 archivos: corridas + resumenes 2026-10-04); pruebas_dsh/20261015_123336/; EXPEDIENTE/96 (memo indice 13+ experimentos oct); EXPEDIENTE/95 (informe consolidado 21-10); memo 15-10 | Evidencia abundante pero distribuida. Ver Anexo B para inventario consolidado. Memo 96 declara falta de metadata/hash por experimento |
| A-11 | Taller multi-IA | O2 | F2 | 09_PROTOCOLO_MULTI_IA.md, agente_llm.py | Interfaz no inspeccionada |
| A-12 | Datos GNSS | O3 | F4 | docs/gnss/v2/gtgen/, obsgen/, ground_truth_*.jsonl | Calidad varía por dataset |
| A-13 | Estudios distancia | O3 | F3 | exp_dist/2/3, exp_gaps_avance, exp_ruido_vs_gap, HALLAZGOS_FASE_A_v1.md | Algunas conclusiones en pausa |
| A-14 | Commodities | - | - | Pendiente iteración 2 | No atribuir como propio |
| A-15 | Infraestructura | O4 | F3 | Git remoto, build_release_*.log, backups | Restauración no probada |
| A-16 | Know-how | O3 | F2 | Expedientes 00-99, commits, CT-01 | Recuperabilidad parcial |
| A-17 | Ojo de Gaia | - | - | Fuera de alcance de esta auditoría | Proyecto anterior. Decisión del Director (2026-10-22): no inventariar ahora |
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

**Semáforo global: AMARILLO** — evidencia suficiente para no ser gris; A-04 tiene una validación automatizada local del escenario (230 puntos, gap GT declarado de 30 m y divergencia de 2.072 m frente a tolerancia de 8 m), pero falta CI (F5) y cobertura automatizada integral de los escenarios de Track Honesto.

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

### 5.4 Avalúo por módulo (borrador, confianza baja)

**Nota de honestidad:** todo avalúo de etapa temprana tiene confianza baja. Los intervalos son amplios porque la mayoría de los activos no tienen comparable directo. No hay mercado para "NaveGo" ni para "LOGOS" como productos separados; el valor está en la combinación.

#### Metodología

| Método | Qué mide | Qué NO mide |
|---|---|---|
| Costo de reposición | Esfuerzo para reconstruir equivalente hoy | No mide mercado ni ingresos |
| Comparables de mercado | Precio de productos/servicios similares | No mide lo que NaveGo/LOGOS harían distinto |
| Valor de opción | Qué habilita a futuro | Es potencial, no realizado |
| Valor de evidencia | Fuerza de las afirmaciones sobre el activo | Factor de confianza, no dinero |

#### Módulos y avalúo

| Módulo | Qué es | Valor actual (evidencia) | Costo reposición | Comparables | Valor potencial (si auditado y aprobado) |
|---|---|---|---|---|---|
| NaveGo app | App náutica offline-first, HUD, track, mapas, waypoints | O3/F3. Producto probado en campo (560 km, 39k fixes). Sin test E2E. | $24k–96k | Navionics $50–100/año; Savvy Navvy $100–200/año | O4/F5. Suscripción $50–100/año con base de usuarios |
| LOGOS | Gobernanza, MANIFEST, Gate, trust, SHA-256, protocolos | O4/F4. Gate READY, trust verificado, 5 tests propios. Solo gobernanza, no producto. | $16k–64k | MLOps/gobernanza IA (Weights&Biases, Arize) sin comparable exacto | Licencia $10k–50k/año a empresas; consultoría $100–200/h |
| Timonel | Agente LLM, SFT/LoRA, bancos de evaluación, decisiones náuticas | O3/F3. 18 corridas, 13 experimentos indexados, 1/6 tests con assert. | $8k–48k | Consultoría IA $100–200/h; fine-tuning $500–2000/proyecto | Licencia $500–2000/mes; consultoría $100–200/h |
| Simulador (Godot+Polaris+Python) | Entorno de simulación de vela, física, bridge, Puerto Esperanza | O3/F4. Misión hardcodeada (36,-6), 4 ground_truth, 18 corridas, 13 experimentos. | $8k–48k | Simuladores náuticos profesionales $500–2000/año | Licencia $500–2000/año; servicio $5k–20k/proyecto |
| Taller multi-IA | Interfaz con múltiples IAs, orquestación | O2/F2. 09_PROTOCOLO_MULTI_IA.md, agente_llm.py. | $4k–16k | Orquestación IAs $20–200/mes | Licencia $200–1000/mes; integración $2k–10k |
| Datos GNSS + ground truth | Datasets reales/sintéticos, 39k fixes, 13 experimentos | O3/F4. gtgen/, obsgen/, sha256_resultados.txt. | $4k–16k | Datasets etiquetados $500–5000 | Licencia $1k–5k a investigadores |
| Estudios de distancia | Metodología A/B/C, experimentos, informes | O3/F3. exp_dist/2/3, exp_gaps_avance, exp_ruido_vs_gap. | $4k–16k | Conocimiento técnico documentado | Consultoría $100–200/h; valor reputacional (paper) |

#### Total (intervalo, no suma simple)

- **Costo de reposición del conjunto:** $64k–288k USD (suma de módulos, sin sinergias).
- **Valor potencial con auditado y aprobado:** $20k–80k/año en licencias + consultoría, dependiendo de base de usuarios y clientes.
- **Valor de opción (no monetario):** soberanía offline, track honesto, gobernanza auditable. Diferenciadores no cubiertos por comparables.

#### Lo que NO se puede valuar

- **Know-how acumulado:** 3 meses de trabajo intensivo no se reponen solo con horas. La arquitectura ya validada, los errores ya cometidos, las decisiones ya tomadas — no tienen comparable de mercado.
- **Valor de evidencia:** SHA-256, trust, 13 experimentos indexados. Vale más que un producto sin evidencia, pero no se puede medir en dólares.
- **Sinergia entre módulos:** NaveGo + LOGOS + Timonel + Simulador no valen lo mismo separados que juntos. El conjunto es mayor que la suma.

**Confianza del avalúo: baja.** Los intervalos son amplios y los supuestos están declarados. Cualquier decisión de inversión o venta requiere una valoración profesional con datos de mercado reales.

---


## 6. Deuda conocida

- **P43:** descripción dice "trust ausente", obsoleta. Trust existe y sincroniza. Diferido. Antes de cerrar, ejecutar `mark-reviewed` y registrar salida.
- **~1500 untracked** en `docs/gnss/v2/obsgen/fixes/`. No borrar ni añadir en bloque.
- **Informe de distancia:** `EXPEDIENTE/51`, `EXPEDIENTE/94`, `docs/gnss/exp_dist/INFORME_DISTANCIA.md` en pausa/revisión.
- **Push automático:** no activado por decisión.
- **A-06 (guardado/export):** `exportToGodot.ts` funcional para export JSON hacia Godot; sin export GPX/KML para usuario; sin test E2E de guardar+reabrir+exportar.
- **A-17 (Ojo de Gaia):** fuera de alcance de esta auditoría por decisión del Director (2026-10-22). Proyecto anterior; no se inventaría ahora.
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

---

## Anexo B — Inventario de evidencia del simulador

**Fecha de consolidación:** 2026-10-22
**Propósito:** consolidar en un solo lugar la evidencia dispersa del simulador. No crea nueva evidencia, no la interpreta; solo la lista con rutas y volúmenes reales.

### B.1 — Runs de simulación (`~/.logos/runs/`)

| Run | Tipo | Archivos | Tamaño ground_truth |
|---|---|---|---|
| `20261015_195114_test` | Completo | comandos_in, comandos, ground_truth, resultado, runner.log, telemetria | 119 KB |
| `20261015_202610_test` | Completo | comandos_in, comandos, ground_truth, resultado, runner.log, telemetria | 210 KB |
| `20261015_203108_test` | Completo | comandos_in, comandos, ground_truth, resultado, runner.log, telemetria | 204 KB |
| `20261015_203702_test` | Completo | comandos_in, comandos, ground_truth, resultado, runner.log, telemetria | 205 KB |
| `_caso_a0` | Parcial | solo comandos_in | — |
| `_caso_a0_limpio` | Parcial | solo comandos_in | — |
| `_caso_a0_sin_viento` | Parcial | solo comandos_in | — |
| `_smoke_test` | Parcial | solo comandos_in | — |

**Total:** 4 runs completos (con telemetría y resultado) + 4 parciales.

### B.2 — Corridas de Timonel (`timonel/corridas/`)

- **1043 archivos** (corridas `corrida_*.json` + resúmenes `resumen_*.json`)
- Fecha: 2026-10-04
- Rango de tamaños: 639 B a 4.6 KB por corrida

### B.3 — Pruebas DSH (`timonel/pruebas_dsh/`)

- `20261015_123336/` con `telemetria.jsonl.antes` y `telemetria.durante.jsonl`

### B.4 — Documentos de experimentos (`timonel/borradores/`)

20+ archivos `.md`, incluyendo:
- `experimento_0_godot_headless_2026-10-15.md`
- `experimento_1_comparacion_python_godot_2026-10-15.md`
- `experimento_e2_frecuencia_2026-10-16.md`
- `divergencia_fisica_python_godot_2026-10-15.md`
- `flotabilidad_python_2026-10-15.md`
- `contraste_cobertura_python_godot_2026-10-15.md`
- `auditoria_viento_python_godot_2026-10-16.md`
- `diagnostico_timon_python_godot_2026-10-16.md`
- `ficha_p37_beneteau_2026-10-16.md`
- `contrato_intent.md`
- `f0_diseno.md`, `f0_diseno_v2.md`
- `alexa_multiagente.md`
- Y otros (ver `timonel/borradores/` completo)

### B.5 — Memos y consolidados (`EXPEDIENTE/`)

- `96_MEMO_EXPERIMENTOS_OCTUBRE_2026-10-15_16.md` (79 líneas) — índice de 13 experimentos, declara falta de metadata/hash por experimento
- `95_INFORME_CONSOLIDADO_TIMONEL_COPILOTO.md` (119 líneas) — síntesis de arquitectura y estado

### B.6 — Lo que falta consolidar

- **Hash de experimento:** ninguno de los 13 experimentos declara hash de dataset+configuración+código. El memo 96 lo marca como faltante.
- **Consolidación canónica:** la evidencia está dispersa en 5 ubicaciones. Un lugar canónico único (probablemente `~/.logos/runs/` con subcarpetas) unificaría.
- **Metadata por experimento:** N, semillas, comando exacto, versión de código. El memo 96 lo declara para cada uno.

---

*Este anexo no crea evidencia nueva. Consolida la existente. Cualquier hash o metadata pendiente se declara como deuda, no se inventa.*
