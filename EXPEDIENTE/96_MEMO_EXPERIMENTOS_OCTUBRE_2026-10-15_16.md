# MEMO ÍNDICE — EXPERIMENTOS Y ANTECEDENTES DE OCTUBRE 2026

**Fecha:** 2026-10-21
**Autoría:** Borrador preparado por asistencia IA. Sujeto a revisión y aprobación del Director.
**Estado documental:** BORRADOR. No se declara CURRENT.
**Naturaleza:** Índice. No es evidencia ni síntesis.
**Complementa:** 95_INFORME_CONSOLIDADO_TIMONEL_COPILOTO.md.
**No declarado en MANIFEST en esta etapa.**

## 0. Propósito

Hacer encontrables los 13 documentos de octubre que viven en timonel/borradores/ sin estructura, sin índice y sin metadata completa. No los mueve. Declara dónde están, qué naturaleza tienen, qué estado real declaran y qué comprobación falta.

No replica resultados. No completa N, hash ni dataset por inferencia.

## 1. Los 13 documentos

| # | Ruta actual | Naturaleza | Estado declarado | Metadata faltante | Verificación pendiente |
|---|---|---|---|---|---|
| 1 | timonel/borradores/experimento_0_godot_headless_2026-10-15.md | Evidencia (registro) | COMPLETADO | N, semillas, comando, hash de experimento | Confirmar qué se midió y con qué configuración |
| 2 | timonel/borradores/experimento_1_comparacion_python_godot_2026-10-15.md | Evidencia | BORRADOR | N, semillas, comando, hash | Verificar predecesores |
| 3 | timonel/borradores/experimento_e2_frecuencia_2026-10-16.md | Evidencia | BORRADOR | N, semillas, comando, hash | Verificar contexto P39 + TIMON_TORQUE=2500 |
| 4 | timonel/borradores/divergencia_fisica_python_godot_2026-10-15.md | Análisis | BORRADOR | No aplica N | Relación con D-0015/0016 desmentida; verificar otras referencias |
| 5 | timonel/borradores/flotabilidad_python_2026-10-15.md | Implementación | BORRADOR | No aplica N | Confirmar código resultante en simulador_polaris.py |
| 6 | timonel/borradores/contraste_cobertura_python_godot_2026-10-15.md | Análisis (inspección) | BORRADOR | No aplica N | Verificar relación con experimento_1 |
| 7 | timonel/borradores/auditoria_viento_python_godot_2026-10-16.md | Auditoría (solo lectura) | BORRADOR | N no declarado | Verificar si el bloqueante sigue activo |
| 8 | timonel/borradores/diagnostico_timon_python_godot_2026-10-16.md | Diagnóstico | BORRADOR | N=15 (3x5) declarado; falta variable medida, resultados y conclusión | No es validación estadística |
| 9 | timonel/borradores/plan_fase_2_2026-10-16.md | Plan | BORRADOR | No aplica N | Verificar dependencia con ficha P37 |
| 10 | timonel/borradores/MEMO_TECNICO_NAVEGO_POLARIS_TIMONEL_2026-10-15.md | Registro técnico de estado y planificación | Estado no declarado (el encabezado declara Tipo, no Estado) | No aplica N | Revisar contradicciones con estado actual |
| 11 | timonel/borradores/bibliografia_evaluacion_simulador.md | Antecedente bibliográfico | BORRADOR | No aplica N | Anomalía: sin fecha en el nombre |
| 12 | timonel/borradores/bibliografia_verificacion_llm_2026-10-15.md | Antecedente bibliográfico | BORRADOR | No aplica N | Verificar que no se mezcle con el 11 |
| 13 | timonel/borradores/ficha_p37_beneteau_2026-10-16.md | Antecedente bibliográfico | BORRADOR, SIN verificar contra PDF | No aplica N | Verificar contra PDF original antes de citar formalmente |

Conteo: 11 BORRADOR + 1 COMPLETADO + 1 sin estado declarado (el 10).

### 1.1 Sobre el hash

Se distingue:
- Hash del archivo Markdown: integridad documental. Se calcula con la herramienta que LOGOS determine.
- Hash del experimento: identifica dataset, configuración y código que produjeron una medición. Permite reproducir.

Ninguno de los 13 declara hoy el segundo. El primero se calcula cuando el documento entre al MANIFEST.

## 2. Advertencias

- El 1 conserva COMPLETADO como estado documental aunque carezca de metadata para reproducibilidad plena. No se falsifica ni se completa por inferencia.
- El 8: N=15 no es validación estadística. Es tamaño de exploración. Falta qué se midió y qué conclusión sostiene.
- Los 4, 5, 6, 7, 8 no son evidencia en sentido estricto: son análisis, implementación, inspección, auditoría o diagnóstico. Se clasifican por naturaleza.
- El 11 sin fecha en el nombre: anomalía menor, no se corrige aquí.
- El 13 marcado SIN verificar contra PDF: se lista como antecedente no validado.
- D-2026-0015 y D-2026-0016: ambas son decisiones de hashing (confirmado por lectura de .logos/decisions/). No tienen relación con divergencia_fisica_python_godot_2026-10-15.md.

## 3. Qué se verificó y qué falta

Verificado por lectura de encabezados (2026-10-21):
- Los 13 existen y tienen ruta confirmada.
- 11 BORRADOR, 1 COMPLETADO, 1 sin estado declarado.
- 12 tienen fecha en el nombre; el 11 no.
- Solo el 8 declara N (15 corridas).
- Ninguno declara hash de archivo ni hash de experimento.

Falta, no se completa por inferencia:
- N, semillas, comando exacto de reproducción donde aplique.
- Hash de dataset de las corridas.
- Fecha de corte para cualquier conteo.
- Confirmación de que el código actual reproduce los resultados reportados.

## 4. Lo que este documento NO hace

No mueve los 13. No crea 05_EVIDENCIA/2026-10_timonel/. No asigna pendientes con numeración (pendiente de cotejo contra PENDIENTES.md). No completa metadata. No reescribe los 13.

## 5. Cuestiones abiertas

Para cotejar contra EXPEDIENTE/PENDIENTES.md antes de numerar:
- Completar metadata (N, hash, comando) donde corresponda.
- Decidir destino definitivo de los 13 cuando tengan metadata.
- Verificar ficha_p37 contra PDF original.
- Verificar consumidores de tipos timonel_consolidado y evidence_index.
- Verificar discrepancia Gate 6 vs 7 checks.
