# MAPA DE ARQUITECTURA — NAVEGO

**Ultima actualizacion:** 2026-10-10
**Proposito:** un solo documento para entender todo el sistema.

## 1. QUE ES CADA COSA

### NAVEGO
La app mobile. React Native + Expo + SQLite.
Objetivo: navegacion autonoma, offline, soberana.
Repo: ~/navego_recuperado

### GODOT (el Simulador)
Laboratorio fisico. Simula el velero Polaris, viento, olas, flotabilidad.
Repo: ~/interfaz
- Flotabilidad por malla (168 puntos de Arquimedes)
- Timon fisico (gira segun angulo + velocidad)
- Velas rotativas (Vela_Mayor Q/E, Foque Z/X)
- Viento segun orientacion de velas (shader pendiente)

### TIMONEL (el agente que navega)
Scripts Python en ~/navego_recuperado/timonel/.
Conecta Godot con Qwen 2.5 Coder 7B via Ollama.
Solo DECIDE (receta, parametro, reaccion). NO ejecuta.

### DSH (el sandbox de agentes)
logos-dsh + carpeta sandbox/.
Agentes LLM trabajan dentro de sandbox_X. No salen de ahi.

### LOGOS (memoria/evidencia)
.logos/bin/. El metodo. NO MIENTE.
- logos-gate: estado del proyecto
- logos-brief: brief de arranque
- logos-arranque: contexto para hilo nuevo
- logos-dsh: arranca agente en sandbox
- logos-mem: capsula de memoria
- logos-reconcile: marca fuentes revisadas
- logos-hash: hashea fuentes
- logos-baseline: establece baseline

### QWEN
Modelo Qwen 2.5 Coder 7B en Ollama (localhost:11434).

## 2. COMO SE CONECTAN

GODOT  <-- telemetria.jsonl -- TIMONEL --> QWEN
          -- comandos.jsonl -->

Regla: un solo escritor por archivo.
- Godot escribe telemetria.jsonl
- Timonel escribe comandos.jsonl

## 3. SCRIPTS DEL TIMONEL

Nucleo:
- timonel.py: intermediario Godot<->Qwen
- timonel_python.py: agente en simulador Python puro
- agente_llm.py: habla con Qwen via Ollama
- simulador_polaris.py: simulador matematico puro
- recetas_navegacion.py: recetas de maniobras
- memoria.py: memoria externa
- runner_entrenamiento.py: N corridas

Evaluacion:
- oraculo.py: oraculo myopic
- oracle_pure_pilot.py: piloto con oraculo
- validacion_oraculo.py: Oracle Validation 001
- benchmark_decisions.py: benchmark local
- determinism_gate.py: determinismo de Ollama

Investigacion:
- runtime_probe.py, runtime_probe_perm.py, runtime_probe_stop.py
- runtime_carryover.py: RUNTIME-CARRYOVER-001 (memo 65)
- cold_warm_investigation.py
- context_sampler.py: banco COMMON_CONTEXT (350)
- test6.py

## 4. HIPOTESIS (H-2026-XXXX)

Formato JSON con: id, observacion, problema, hipotesis, prediccion,
experimento, criterio_falsacion, costo_estimado, riesgo, reversible, estado.

Viven en:
- Historico: backups/SESION_2026-09-25/logos-hypotheses/
- Informes: EXPEDIENTE/hallazgos/

## 5. DECISIONES (D-2026-XXXX)

JSON congelado en .logos/decisions/:
- D-0001 a D-0008: GNSS, persistencia, SQLite
- D-0009: 5 estados del Gate (reviewed_against_commit)
- D-0010: Freshness por hash de contenido

## 6. MEMOS DEL TIMONEL (57-66)

Leer en orden:
- 57: Diseno del Timonel
- 58: Investigacion nautica
- 59: LLM Notebook extra
- 60: Diseno experimental memoria v1
- 61: Revision 1 (regret vs accuracy)
- 62: Revision 2 (COMMON-CONTEXT)
- 63: Defecto de retrieval
- 64: Cambio de regimen durante benchmark
- 65: RUNTIME-CARRYOVER-001
- 66: Estado de sesion 2026-10-05

Regla: memos NO se reescriben. Cada uno corrige al anterior.

## 7. SANDBOXES

- sandbox/: datos generales
- sandbox_corredor/: analisis RN9
- sandbox_refactor_mapas/: refactor mapas
- sandbox_refactor_glyphs/: refactor glifos
- sandbox_refactor_provincias/: refactor provincias

Regla: dentro del sandbox el agente escribe. Fuera, NO.

## 8. BRIDGES

- bridge.py (puerto 8084): HTTP, estado en navego_state.json
- voice_bridge.js: Node, token NAVEGO-2026-LOGOS
- timonel_bridge.gd: dentro de Godot, canal bidireccional

## 9. ARRANCAR SESION DE NAVEGACION ASISTIDA

1. Verificar Gate: ./.logos/bin/logos-gate NAVEGO
2. Contexto hilo: ~/.logos/bin/logos-arranque
3. Arrancar Godot: cd ~/interfaz && abrir proyecto con F5
4. Arrancar Timonel: python3 timonel/timonel.py
5. Ver telemetria: tail -f ~/.local/share/godot/app_userdata/interfaz/timonel/*.jsonl
6. Correr benchmark: python3 timonel/runner_entrenamiento.py --n 20
7. Analisis en timonel/corridas/*.json

## 10. QUE FALTA HOY (2026-10-10)

- Godot: shader de viento (memo 67)
- Godot: reconciliar simulator_source
- Timonel: ejecutar RUNTIME-CARRYOVER-001 (memo 65)
- Timonel: rehacer benchmark de memoria
- Timonel: sistematizar hipotesis (hoy dispersas)

## 11. REGLAS DURAS

1. Un cambio -> una verificacion -> una evidencia.
2. No inventar datos. Si no se sabe, se dice "no se".
3. Backup .pre-<etapa> antes de tocar codigo.
4. El codigo va al chat, no a bash.
5. Los .pre-* NO se borran sin permiso.
6. Un solo escritor por archivo.
7. Hipotesis antes de experimento. Criterio de falsacion ANTES.
8. Los memos NO se reescriben.
9. Gate WARNING opcional no bloquea. Gate BLOCKED si.

## 12. SI TE PERDES, EMPEZA POR ACA

1. Este archivo.
2. EXPEDIENTE/66_ESTADO_SESION_2026-10-05.md
3. EXPEDIENTE/57_DISENO_TIMONEL_ENTRENAMIENTO.md
4. ~/.logos/bin/logos-arranque
5. ./.logos/bin/logos-gate NAVEGO

---

## 13. MODOS DE OPERACION

### Modo MANUAL (default)
El usuario controla el barco con el teclado:
- W/S: avance/retroceso
- A/D: timon
- Q/E: vela mayor
- Z/X: foque
- Timonel Python: APAGADO
- timonel_bridge.gd: sin comandos nuevos, no hace nada.

### Modo AUTONOMO
Timonel Python controla el barco:
- Timonel escribe comandos.jsonl
- timonel_bridge.gd lee y aplica torque/fuerza
- El usuario NO toca teclas
- Consume RAM (Ollama + Qwen)

### Como se togglea
No hay toggle automatico. El usuario prende/apaga el proceso Python.

### Fase actual del Timonel
- Fase 1 (comandos fijos): HECHA
- Fase 2 (piloto Python simple, timon_python): EN USO
- Fase 3 (LLM decidiendo via Qwen): CODIGO ESCRITO, NO CONECTADO

### Scripts del control manual (Godot)
- main.gd: W/S (avance/retroceso). A/D DESACTIVADO (ahora lo maneja rudder_controller).
- rudder_controller.gd: A/D -> timon visual + torque fisico proporcional.
- sail_controller.gd: Q/E -> vela mayor, Z/X -> foque.
- timonel_bridge.gd: canal bidireccional con Timonel Python (solo si el Timonel corre).

### Modelo Qwen
- Codigo timonel.py usa: qwen2.5-coder:3b
- Memo 57 dice: Qwen 2.5 Coder 7B
- PENDIENTE: verificar cual es el que se usa hoy.

---

## 14. ESTADO DEL TIMON FISICO (2026-10-10)

### Valores finales en Godot
- `rudder_controller.gd` -> `torque_max = 5500`
- `main.gd` -> A/D DESACTIVADO (no duplica torque)
- Vuelta 360 grados a 9.1 kn: ~70 segundos
- Radio de giro variable con velocidad:
  - 9 kn -> radio ~28 m
  - 5 kn -> radio ~15 m
- Rango validado como realista para velero de 10m.

### Regla nautica aprendida
La tasa de giro (grados/s) es aproximadamente constante.
Lo que cambia con la velocidad es el RADIO del giro, no el tiempo.
A menos velocidad -> radio mas cerrado -> maniobra mas precisa.
Por eso los patrones reales bajan velocidad al entrar a puerto.

### Lo que NO se toca
- El modelo Qwen sigue en 3B (timonel.py) segun el codigo.
  Memo 57 dice 7B. PENDIENTE: verificar.

### Como se togglea manual vs autonomo
Ver seccion 13. Timonel Python apagado = modo manual (teclado).
