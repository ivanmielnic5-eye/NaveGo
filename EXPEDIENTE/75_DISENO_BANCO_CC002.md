# DISENO DEL BANCO COMMON_CONTEXT_002

**Fecha:** 2026-10-10
**Autor:** Directora de Investigacion
**Estado:** CONGELADO. Base para implementar el generador.
**Complementa:** memos 73 y 74.

---

## 0. Proposito

Disenar el banco nuevo que va a servir como ground truth del benchmark. Reemplaza a COMMON_CONTEXT_001 (350 contextos sin provenance verificable).

---

## 1. PRINCIPIOS

1. Separacion fisica entre lo que ve el LLM y las etiquetas del oraculo.
2. Etiquetas calculadas por el oraculo, NO asignadas por el generador.
3. Unicidad: solo se aceptan contextos con decision unica + margen.
4. Provenance: cada contexto lleva metadata reproducible.
5. Sin leakage: el prompt del LLM NO contiene la respuesta.
6. Viento constante por contexto (condicion principal).
7. Sin historial, sin experiencias.

---

## 2. TRES ARCHIVOS

### banco_contextos.jsonl (visible al LLM)

Un contexto por linea. Es lo que se usa para armar el prompt.

{
  "context_id": "CC002-000001",
  "state": {
    "pos_x": float, "pos_z": float,
    "hdg": float, "sog": float,
    "meta_x": float, "meta_z": float,
    "viento_kn": float, "viento_dir": float
  },
  "schema_version": "1.0",
  "state_hash": "sha256:..."
}

### banco_etiquetas.jsonl (acceso restringido al evaluador)

Un label por contexto. NO se incluye en el prompt.

{
  "context_id": "CC002-000001",
  "oracle_version": "2.0",
  "accion_optima": "ir_a_punto",
  "parametro_oraculo": [x, z] o float o null,
  "scores_por_accion": {
    "corregir_rumbo": {...},
    "ir_a_punto": {...},
    "frenar": {...},
    "terminar": {...}
  },
  "margen_vs_segunda": float,
  "label_status": "UNIQUE" | "AMBIGUOUS",
  "familia": "lejos|medio|cerca|terminal",
  "split": "desarrollo" | "confirmatorio"
}

### banco_manifiesto.json

Metadata global del banco.

{
  "version": "CC002-1.0",
  "fecha_generacion": "ISO8601",
  "seed": int,
  "oracle_version": "2.0",
  "simulator_version": "sha256:...",
  "recetas_version": "sha256:...",
  "umbral_unicidad_m": 2.0,
  "n_candidatos_generados": int,
  "n_contextos_finales": int,
  "n_descartados": {
    "terminal_invalido": int,
    "boundary_violation": int,
    "margen_insuficiente": int,
    "duplicado": int,
    "otro": int
  },
  "split_counts": {"desarrollo": int, "confirmatorio": int},
  "accion_counts": {"corregir_rumbo": int, "ir_a_punto": int, "frenar": int, "terminar": int},
  "hash_contextos": "sha256:...",
  "hash_etiquetas": "sha256:..."
}

---

## 3. PROCESO DE GENERACION

### Fase 1 — Generar candidatos (con semilla)

- 2000 candidatos con random seed fija.
- Distribucion uniforme de:
  - Distancia a meta: 15m a 250m.
  - Heading: 0 a 360 grados.
  - SOG: 0 a 8 nudos.
  - Direccion de meta: 0 a 360 grados (relativa al origen).
  - Viento: 0, 5, 10, 15 kn.
  - Direccion de viento: 0 a 360 grados.
- Estado inicial: barco en (0,0) mirando a heading aleatorio.

### Fase 2 — Calcular etiquetas con el oraculo

Por cada candidato:
- Correr oraculo ampliado con las 4 acciones.
- Registrar: accion optima, parametro, scores, margen vs segunda.

### Fase 3 — Filtrar

Descartar candidatos con:
- `boundary_violation = True`.
- `terminar` invalido (si terminar es el ganador pero dist >= 15m, no aplica: terminar solo vale si dist < 15m).
- Margen vs segunda < umbral (2.0 metros de progreso medio).
- Duplicados exactos (mismo state_hash).

### Fase 4 — Balancear por accion

De los sobrevivientes:
- Tomar 75 por accion para desarrollo.
- Tomar 75 por accion para confirmatorio.
- Total: 600 (300 desarrollo + 300 confirmatorio).
- Si no alcanzan 75 de alguna accion, reducir todas proporcionalmente.
- Descartar el resto (se guardan en el manifiesto).

### Fase 5 — Split

Split aleatorio por accion con seed fija. Nunca un contexto de desarrollo aparece en confirmatorio.

---

## 4. UMBRAL DE UNICIDAD

- Umbral inicial: 2.0 metros de progreso medio.
- Variable configurable en el generador.
- Se documenta como hipotesis.
- Analisis de sensibilidad DESPUES de generar: ver cuantos contextos se aceptan con umbral 0.5, 1.0, 2.0, 5.0.
- Si el umbral rechaza mas del 80% de candidatos, revisar.

---

## 5. VALIDACION (10 CHEQUEOS)

Antes de usar el banco:

1. Integridad: todos los estados cumplen el esquema.
2. Reproducibilidad: mismo seed + versiones -> mismo banco.
3. Cobertura: 4 acciones presentes en desarrollo y confirmatorio.
4. Unicidad: todos con margen >= umbral.
5. Duplicados: no hay state_hash repetido.
6. Contrafactuales: pares con una variable cambiada dan transiciones coherentes.
7. Sin leakage: el prompt generado NO contiene la respuesta.
8. Parser: probar los 13 casos del parser (memo 72).
9. Auditoria ciega: revision manual de 20 contextos.
10. Balance: no hay accion sobrerrepresentada en ninguna familia.

---

## 6. FAMILIAS DE ESTADOS

Cuatro familias, definidas por distancia a meta:
- TERMINAL: dist < 15m.
- CERCA: 15m <= dist < 50m.
- MEDIO: 50m <= dist < 150m.
- LEJOS: dist >= 150m.

Se registran en el label. Se usan para analisis estratificado.

---

## 7. LO QUE NO SE HACE

- NO se incluye la accion esperada en el contexto visible.
- NO se incluyen scores ni ranking del oraculo en el contexto.
- NO se inventan etiquetas para balancear.
- NO se aceptan empates como unicos.
- NO se ajusta el prompt mirando el confirmatorio.
- NO se mezclan contextos de desarrollo y confirmatorio.
- NO se incluyen historial ni experiencias.

---

## 8. LO QUE FALTA MEDIR

- Variabilidad real del oraculo entre corridas (con viento constante, deberia ser 0).
- Si el 80% de candidatos cae por margen, revisar umbral.
- Distribucion de acciones en los 2000 candidatos.

---

## 9. IMPLEMENTACION

Archivo a crear: `timonel/generar_banco_cc002.py`.
Usa: `oraculo.py` (ampliado), `simulador_polaris.py`, `recetas_navegacion.py`.
Salida: 3 archivos en `timonel/banco_cc002/`.

Despues del banco: cualificar el runtime (paso 5 del memo 73).

---

## 10. FIRMA

**Estado:** CONGELADO.
**Proximo paso:** implementar generador.
**Regla:** el banco confirmatorio no se toca hasta cualificar el runtime.
