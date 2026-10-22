# INFORME CONSOLIDADO — TIMONEL Y EL COPILOTO

**Fecha:** 2026-10-21
**Autoría:** Borrador preparado por asistencia IA. Sujeto a revisión y aprobación del Director.
**Estado documental:** BORRADOR. No se declara CURRENT ni se instala como fuente autoritativa hasta aprobación explícita.
**Naturaleza:** Síntesis de arquitectura y estado. No es evidencia experimental.
**Reemplaza como documento de referencia a:** 71_ESTADO_REAL_TIMONEL.md (2026-10-10) y 89_MEMO_CONSOLIDADO.md (2026-10-11). Ambos se conservan sin edición. No se declara cadena de sucesión entre ellos porque no está documentada.
**Predecesores referenciados:** 48, 57, 58, 59, 71, 86, 87, 88, 89, 90, 91.
**No declarado en MANIFEST en esta etapa.**

## 0. Propósito y alcance

Centralizar el conocimiento sobre Timonel, Polaris (Godot), simulador Python, DSH y Agente LLM, con puerta de entrada única al estado actual.

Qué hace: sintetiza arquitectura, estado verificado, riesgos y precondiciones. Cada afirmación remite a su fuente.

Qué NO hace: no replica resultados experimentales, no reemplaza expedientes de evidencia, no declara números propios.

## 1. Identidad y procedencia (observado 2026-10-21)

| Repositorio | Ruta | Rama | HEAD completo | Árbol |
|---|---|---|---|---|
| NaveGo | ~/navego_recuperado | v2-track-honesto | 5e4c6bb475bdc6b75f5727b500aabdcedc7f4716 | 5 modificados |
| Godot | ~/interfaz | experimento-godot | dd5754e19ee62b63e5a2a51b8ad80686fbda75b4 | 2 untracked |

Modificados NaveGo: EXPEDIENTE/BRIEF_NAVEGO.md, EXPEDIENTE/BRIEF_NAVEGO_pegable.txt, docs/gnss/v2/eval/methods.py, docs/gnss/v2/eval/run_all.py, docs/gnss/v2/gtgen/gen_traj.py.

Untracked Godot: runner_headless.gd.uid, test_input.gd.uid.

Hash del simulador declarado en MANIFEST: 9a6e50eb7299b7ae6ba17f2d55d34b5756e52d43c9a873b637361fc5cc67c09e.

El conjunto exacto de archivos que ese hash cubre no está demostrado en este documento.

## 2. Arquitectura

### 2.A Capas de producto

No se enumeran. La fuente canónica que fija las capas de madurez del copiloto no fue localizada entre los expedientes 27, 28, 53 y 54. No se elige por aproximación.

### 2.B Componentes técnicos

1. Entorno físico Godot (Polaris): ~/interfaz/scripts/, main.tscn; float_cube.gd, wind.gd, water.gd, rudder_controller.gd, sail_controller.gd.
2. Simulador rápido Python: timonel/simulador_polaris.py. 168 puntos de
   flotación vía hull_mesh.json (commit 31e0e1a, 2026-10-15). Roll y pitch
   implementados. Velas no implementadas (P36). Drag lineal. TIMON_TORQUE
   = 2500 desde c544da9 (2026-10-16). Compartir la malla de 168 puntos no
   implica equivalencia del modelo físico completo.
3. Lógica de control: timonel/acciones.py, controlador_pid.py, recetas_navegacion.py.
4. Entrenador y bancos: timonel/entrenador.py, entrenador_v2.py, generar_banco_*.py.
5. Agente LLM y contratos: timonel/agente_llm.py, memoria.py, D-2026-0011.
6. DSH Harness: infraestructura transversal. Referencias: EXPEDIENTE/23_ESPEC_LOGOS_DSH.md, EXPEDIENTE/48_TIMONEL_DSH.md. No es capa de producto.

## 3. Estado verificado

| Afirmación | Fuente | Estado |
|---|---|---|
| En la ejecución del 15/10, timonel.py llamaba a timon_python(); consultar_dsh() estaba configurada con qwen2.5-coder:3b pero no se llamaba desde el ciclo principal | MEMO_TECNICO_NAVEGO_POLARIS_TIMONEL_2026-10-15.md | Hecho histórico acotado a esa ejecución. No se generaliza al estado vigente |
| P39 (deadlock de arranque con heading desalineado) | EXPEDIENTE/PENDIENTES.md línea 408; commits c544da9 (2026-10-16) y 39630d6 | RESUELTO con alcance acotado: arranque >45°, 30 corridas con dist_recorrida>0 y meta alcanzada. No afirma cobertura universal |
| D-2026-0015 es decisión de hashing (extraer lógica a módulo compartido, corregir P29) | .logos/decisions/D-2026-0015.json | CONGELADA. Sin relación con divergencia física |
| D-2026-0016 es decisión de hashing del Gate (unificar logos_hash_lib.py, propagar HashError) | .logos/decisions/D-2026-0016.json | CONGELADA. Sin relación con divergencia física |
| Bug de comparación de recetas de duraciones distintas corregido en entrenador_v2 | 87_CORRECCION_BUG_ENTRENADOR.md, 88_DISENO_ENTRENADOR_V2.md | Corregido según memo. D-2026-0012 exige auditoría previa a reuso |
| El oráculo se renombró a Entrenador | 86, 87, 88 | Documentado |
| Los valores de masa configurados coinciden numéricamente en 8000; las unidades del parámetro Python no están declaradas. El centro de masa configurado se informa como (0, -1.2, 0) en ambos entornos | simulador_polaris.py:28,31; main.tscn:85 | Observado. Coincidencia de configuración, no equivalencia dimensional ni física |
| Timón: Python calcula el torque a partir de TIMON_TORQUE = 2500 multiplicado por la orden y un factor de efectividad max(speed_factor, prop_wash_factor). Godot, en la ruta del puente de Timonel, aplica una magnitud nominal de 2500 mientras la orden está vigente, con inversión de signo en el puente | simulador_polaris.py:256-263; timonel_bridge.gd:154-157 | Observado. Misma constante nominal, respuestas dinámicas no equivalentes |
| Cobertura distinta: viento sobre velas solo en Godot; prop_walk solo en Python | contraste_cobertura §2 | Observado. Diferencias de modelo, no defectos |
| Inercia distinta: 53333 en Python (BoxShape 4x1x8), 72667 en Godot (BoxShape 3x1.5x10) | diagnostico_timon §8.2 | Valores de los modelos respectivos, no medición de la inercia real del velero. Factor 1.36x |
| Godot headless: frecuencia efectiva medida de 48.54 Hz en la corrida del 15/10 | experimento_0 §5 | Observado históricamente en una corrida. Distinto del valor nominal configurado de 60 Hz |
| Convención de viento: eje N-S invertido entre Python y Godot. Torque de viento explícito en Python, ausente en Godot | auditoria_viento (16/10) | Observado. Opción 4 aprobada (solo prueba aislada de velas) |

No se citan aquí los porcentajes (100%, 51.5%, 97.7%) porque sus fuentes no declaran N, fecha de corte ni hash de dataset.

No se citan aquí los conteos 894/6.292 ni las cifras 1 s, 48 Hz, 5 ms porque carecen de fecha de corte o N declarado. Su procedencia no se borra de los antecedentes; no se resumen como estado actual.

## 4. Riesgos y discrepancias

- P34/P35 — Divergencia Python–Godot. PENDIENTE en PENDIENTES.md. Decisión de unificar física o declarar usos distintos sigue abierta. Naturaleza de la divergencia: drag lineal en Python, cuadrático en Godot. Comparar coeficientes aislados (×24 lateral, ×70 angular) no determina la fuerza relativa en todos los regímenes de velocidad. El documento divergencia_fisica (15/10) describe un estado anterior al configurado tras la migración registrada en 31e0e1a; su secuencia temporal exacta respecto del commit no está verificada.
- Gate: discrepancia documental confirmada. Registro del 19/10 muestra 7 checks con trust: OK; salida del 21/10 muestra 6 sin Trust. El historial del binario no muestra commit posterior al 19/10 que explique el cambio. No se atribuye a P44. Comportamiento actual no declarado sin inspeccionar el binario vigente.
- Seis capas de producto: fuente no localizada.
- Tipos timonel_consolidado y evidence_index: no introducidos en MANIFEST. Sin verificar consumidores (logos-mem, logos-brief, Gate).
- Unidades del torque no verificadas. TIMON_TORQUE (Python) y timon_torque (Godot) no declaran unidad. La coincidencia numérica en 2500 no establece equivalencia dimensional.
- Constantes físicas sin calibración validada contra datos reales. EXPEDIENTE/58 (4/10) es informe bruto de referencia del LLM Notebook, no calibración acreditada.
- flotabilidad_python_2026-10-15.md describe un estado intermedio (resorte de 2 puntos) reemplazado por 168 puntos dentro del mismo commit 31e0e1a. El documento no refleja el código que él mismo introduce.

P39 no figura como riesgo activo: está RESUELTO con alcance acotado (ver sección 3).

## 5. Precondiciones

- D-2026-0012 (CONGELADA): auditar el Entrenador antes de entrenar con él. Precondición directa del banco A4. A4 no se inicia sin cumplirla.
- Fase 2 (navegación a vela): plan en plan_fase_2_2026-10-16.md (BORRADOR).
- Fase 3 (conectar LLM): requiere banco A4 con Contrato Intent, sujeto a D-2026-0012.

## 6. Relación con antecedentes

71_ESTADO_REAL_TIMONEL.md (2026-10-10): se conserva íntegro. Este documento lo supersede como referencia de estado, sin editarlo.
89_MEMO_CONSOLIDADO.md (2026-10-11, mod. 2026-10-14): se conserva íntegro. Este documento lo supersede como referencia de estado, sin editarlo.
48, 57, 58, 59, 86, 87, 88: antecedentes directos referenciados, no modificados.
90_CIERRE_HILO_2026-10-14.md, 91_HITO_FUNCIONAL_NAVEGO_2026-10-17.md: contexto inmediato.

No se agrega campo superseded_by al MANIFEST en esta etapa.

D-2026-0015 y D-2026-0016: ambas son decisiones de hashing. Ninguna tiene relación con divergencia_fisica_python_godot_2026-10-15.md.

Antecedentes adicionales consultados (22/10):
- divergencia_fisica (15/10): estado anterior a la migración de 31e0e1a. No usar como estado actual sin contrastar con el código.
- diagnostico_timon (16/10): post-migración. Fuente de las diferencias de timón, inercia y velocidad de giro.
- contraste_cobertura (15/10): tabla de cobertura por simulador.
- auditoria_viento (16/10): convención de viento invertida. Pendiente de resolución.
- experimento_0 (15/10, COMPLETADO): infraestructura headless. Frecuencia efectiva medida.
- EXPEDIENTE/58 (4/10): informe bruto de referencia. Material de calibración, no calibración validada.

## 7. Lo que este documento NO hace

No mueve archivos. No modifica 71 ni 89. No crea PENDIENTES_TIMONEL.md. No toca timonel/. No toca los 49 .md de raíz. No crea el campo domain. No declara tipos nuevos como vigentes.

## 8. Declaración

Autoridad propuesta: autoritativa para estado consolidado de Timonel al 2026-10-21, sujeta a aprobación. No autoritativa para resultados experimentales, decisiones ni pendientes.

Estado documental: BORRADOR, propuesto, sujeto a aprobación del Director.
