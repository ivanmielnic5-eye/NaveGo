# P1 — Auditoría estática de contratos y puentes Polaris–Timonel

Fecha: 2026-10-24
Repositorio: navego_recuperado
Rama de referencia: v2-track-honesto
HEAD registrado al inicio de P1: 64b2b69463c36813f2b333c26c58dd7307ac2dff

Estado: BORRADOR DE AUDITORÍA.
Revisión y aprobación del Director pendientes.
Este documento no homologa el sistema ni autoriza cambios de código.

## 1. Alcance

Inspección estática de contratos, validador, puente Python,
ejecutor Bubblewrap, pruebas existentes, configuración de misión
y puente original de Godot.

No se modificó código, no se ejecutaron pruebas ni simulaciones
en esta revisión, no se consultó Ollama y no se utilizó la GPU.

La evidencia integrada de Bubblewrap registrada el 2026-10-23
es un antecedente previo; no fue repetida en esta revisión.

## 2. Hechos confirmados

### Contrato y puente Python

- action_schema.json permite read_file y list_dir y exige
  requested_effect=read_only; rechaza propiedades adicionales.
- validate_contract valida el JSON, la estructura y la ruta
  objetivo, incluidos varios casos de escape del workspace.
- simulate_polaris_pipeline valida y genera argumentos;
  no ejecuta Bubblewrap.
- sandbox_executor.py restringe su prueba a read_file sobre
  informe.txt, compara la ruta resuelta y exige coincidencia
  exacta con una lista de argumentos Bubblewrap autorizada.
- La ejecución real de esa prueba usa un archivo sintético,
  /usr/bin/cat, montajes de solo lectura y un timeout.
- Los cinco guardrails de test_sandbox_executor.py sustituyen
  la consulta al modelo y subprocess.run por mocks. Demuestran
  el rechazo sin ejecución para esos casos, no el aislamiento
  completo del sistema.

### Puente original de Polaris

- ~/interfaz/scripts/timonel_bridge.gd y
  tests/fase2/polaris_bridge.py son componentes distintos.
- El puente original lee comandos.jsonl y aplica torque y fuerza
  a partir de timon, avance, timon_ms y avance_ms.
- El consumidor original convierte esos campos a enteros, pero
  en el fragmento inspeccionado no limita sus rangos ni duración.
- _last_command_t comienza en cero y se compara con el campo t.
  No se observa una comprobación de antigüedad respecto del reloj.
- Si el archivo conserva una última orden no nula al reiniciar,
  existe la posibilidad condicionada de aceptarla una vez y
  recalcular su vencimiento desde el momento del reinicio.
  No se ha demostrado que esto haya ocurrido en una corrida.
- La repetición periódica de órdenes nuevas forma parte del
  ciclo de control y no debe confundirse con una orden antigua
  reactivada al reiniciar.

En la versión inspeccionada de timonel.py, main() usa el
controlador determinista timon_python(), con ciclo de 3 s y
órdenes de 1.500 ms. consultar_dsh() está definida, pero no
es llamada por ese main(). Esto describe el código inspeccionado,
no necesariamente todas las versiones históricas ejecutadas.

### Misión y coordenadas

- La meta del controlador utiliza X/Z = (36, -6).
- main.tscn y el comentario de la cámara ubican el muelle actual
  en (36, 2, -6); la diferencia corresponde a la coordenada Y.
- El marcador visual anterior de (200, 0, 0) pertenece a una
  función cuya llamada está desactivada.
- MisionConfig carga, valida parcialmente, calcula un hash y
  congela la estructura.
- El validador propio no aplica todas las reglas de tipos,
  unidades y rangos declaradas por el esquema.
- Las pruebas visibles de test_mision_config.py se concentran
  en propiedades del hash canónico.
- No se localizó la implementación de fusión Intent →
  EffectiveMissionConfig en el código Python consultado;
  sí hay referencias en borradores de diseño.

## 3. Discrepancias y riesgos pendientes

P1-01 — Los protocolos del puente original y del puente Python
de pruebas son distintos; no existe integración demostrada
entre el contrato de acciones y el puente físico original.

P1-02 — El puente original no impone en el receptor límites
explícitos de magnitud y duración ni verifica antigüedad de
órdenes. La posible reactivación de una orden persistida al
reiniciar sigue condicionada y requiere análisis específico.

P1-03 — La validación de MisionConfig es parcial y no aplica
todas las restricciones declaradas en mision_schema.json.

P1-04 — La fusión de Intent y MisionConfig en una configuración
efectiva no fue localizada en el código consultado.

P1-05 — Las pruebas unitarias inspeccionadas cubren casos
concretos y algunos flujos simulados. No equivalen a una
homologación general.

## 4. Decisiones pendientes del Director

- Determinar si se autoriza una prueba aislada del caso de
  reinicio y orden persistida.
- Determinar si se añaden límites de validación en el receptor
  original, preservando el comportamiento normal del controlador.
- Resolver cómo y dónde se implementará la fusión de misión
  efectiva, si procede.
- Decidir separadamente si se conectan los dos protocolos.

Hasta decisión explícita, no modificar ni reemplazar los puentes,
no conectar protocolos y no declarar homologación.

## 5. Próximo paso propuesto

Cerrar la revisión estática como inventario de hechos y pendientes.
Si el Director lo aprueba, abrir una fase separada para analizar
el caso de reinicio en un entorno aislado, sin alterar la
automatización funcional ni ejecutar modelos durante el análisis.


## P1-06 — Rutas de ejecución no unificadas

**Estado:** discrepancia estática comprobada; impacto operativo pendiente de verificación.

### Hechos observados

- `interfaz/scripts/timonel_bridge.gd` lee `NAVEGO_RUN_DIR` para seleccionar la carpeta de telemetría y comandos; si la variable está vacía, utiliza `user://timonel`.
- `timonel/timonel.py` construye `GODOT_DIR` a partir de `~/.local/share/godot/app_userdata/interfaz/timonel` y define desde allí sus rutas de telemetría y comandos. En el código inspeccionado no se observó que consuma `NAVEGO_RUN_DIR`.
- `timonel/simulador_polaris.py` sí contempla `NAVEGO_RUN_DIR`.
- La prueba integrada de `tests/fase2/sandbox_executor.py` corresponde a otro flujo: ejecuta una lectura restringida mediante Bubblewrap. Su resultado no demuestra que el controlador original y el puente Godot compartan las mismas rutas.

### Discrepancia

El puente Godot y el controlador Python original no muestran una configuración común de rutas mediante `NAVEGO_RUN_DIR`.

### Riesgo condicionado

Si se inicia el puente Godot con `NAVEGO_RUN_DIR` apuntando a una carpeta aislada, mientras `timonel/timonel.py` continúa utilizando su ruta fija, ambos componentes pueden leer y escribir archivos distintos. En ese escenario, el controlador no quedaría conectado al puente por esos archivos.

Esto es un riesgo derivado del código inspeccionado, no un fallo reproducido durante esta auditoría. No se descarta que exista un mecanismo adicional de configuración fuera del código revisado.

### Verificación pendiente

Comprobar, en una ejecución autorizada y controlada, qué rutas efectivas utiliza cada componente y si coinciden. No se realizó esa prueba durante esta auditoría estática.

### Decisión pendiente del Director

Definir si se unifican las rutas mediante una configuración compartida y explícita. No se propone modificar código hasta recibir aprobación específica.

## Aclaración de P1-06 — Flujo headless y rutas

**Estado:** discrepancia acotada; no se ha demostrado una desconexión en el flujo headless configurado.

### Evidencia adicional

- `project.godot` declara `RunnerHeadless` como Autoload y establece `main.tscn` como escena principal.
- `run_headless.sh` crea una carpeta de corrida, copia `comandos_in.json`, exporta `NAVEGO_RUN_DIR` y lanza Godot.
- `runner_headless.gd` lee esa carpeta, valida la entrada y escribe `comandos.jsonl`.
- `timonel_bridge.gd` selecciona `comandos.jsonl` y `telemetria.jsonl` a partir de la misma variable de entorno cuando está definida.

### Interpretación revisada

El código inspeccionado muestra una ruta coherente entre el lanzador, el runner y el puente Godot. No se ha ejecutado una corrida nueva durante esta auditoría para verificar su comportamiento efectivo.

`timonel/timonel.py`, en cambio, construye sus rutas a partir de una carpeta fija y no se observó que consumiera `NAVEGO_RUN_DIR`. Esto sería relevante si se pretendiera conectar ese controlador Python al flujo aislado. No se ha establecido que esa combinación forme parte del diseño previsto.

**Pendiente:** verificar el comportamiento efectivo solo si se autoriza una prueba específica. No se propone modificar código en esta etapa.

## P1-07 — Timeout exportado no consumido

**Estado:** discrepancia estática observada; impacto pendiente de verificación.

### Hechos observados

- `run_headless.sh` exporta `NAVEGO_RUN_TIMEOUT_MS`, con valor predeterminado de `120000`.
- En el código inspeccionado de `runner_headless.gd`, `_timeout_ms` se inicializa con `120000`.
- En los fragmentos revisados no se observó que el runner lea `NAVEGO_RUN_TIMEOUT_MS`.
- El lanzador también usa `timeout 180` como límite externo para el proceso Godot.

### Riesgo

Cambiar `NAVEGO_RUN_TIMEOUT_MS` podría no modificar el timeout interno del runner. El límite externo del proceso constituye una segunda protección temporal, pero no reemplaza necesariamente la semántica del timeout interno.

No se ha probado el comportamiento en ejecución ni se ha demostrado que el valor configurable sea un requisito aprobado.

### Pendiente

Determinar si la variable exportada debe controlar el timeout interno o si es un residuo de configuración. No modificar código hasta contar con una decisión explícita.

## P1-08 — Indicador de inicialización inconsistente

**Estado:** inconsistencia lógica estática observada.

### Hecho observado

En `runner_headless.gd`, `_cerrar()` calcula `exito_inicializacion` mediante:

`_comandos_escritos > 0 or _idx_comando == 0`

En rutas de error temprano que conservan `_idx_comando == 0`, la expresión puede evaluar a `true`, incluso cuando la causa de cierre indica un error, como entrada ausente o validación fallida.

### Consecuencia

`resultado.json` puede presentar `exito_inicializacion: true` junto con una causa de cierre de error. Esto reduce la fiabilidad del resultado como evidencia de inicialización.

No demuestra que se hayan aplicado órdenes físicas incorrectas. Es una inconsistencia del indicador de estado.

### Pendiente

Definir y comprobar una semántica inequívoca para los estados de inicialización y ejecución. No modificar código ni reinterpretar resultados históricos sin revisar las evidencias correspondientes.

## Estado de autorización

Estos hallazgos se incorporan como resultados de auditoría estática, no como autorización de cambios de implementación. Las decisiones técnicas y cualquier prueba posterior siguen pendientes de aprobación explícita del Director.

---

## 9. Cierre Documental de la Etapa P1

**Fecha de cierre:** 2026-10-24
**Estado:** AUDITORÍA ESTÁTICA FINALIZADA. PENDIENTE DE DECISIONES TÉCNICAS Y VERIFICACIÓN DINÁMICA.

Tras registrar 8 hallazgos (P1-01 a P1-08), se determina cerrar la etapa de búsqueda estática para evitar parálisis por análisis. 

**Distinción de Hallazgos:**
- **Riesgos de configuración/documentación:** Discrepancias de rutas o falta de contratos claros (Hipótesis estáticas).
- **Riesgos demostrados:** Ninguno ha sido reproducido dinámicamente en esta etapa.

**Próximos Pasos (Separados y sujetos a autorización del Director):**
1. Revisión de este documento por el Director.
2. Decisiones técnicas: definir qué hallazgos requieren cambios de código y cuáles son aceptables.
3. Verificación dinámica: autorizar pruebas específicas para comprobar las hipótesis.
