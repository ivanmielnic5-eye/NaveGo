<!-- ingesta: 2026-10-13 19:48 -->
# BORRADOR — DISENO DE F0 (v2, CONSOLIDADO)

**Fecha:** 2026-10-13
**Estado:** BORRADOR. Fuera del expediente hasta congelar.
**Origen:** consolidacion de Claude + Luna (3 rondas cruzadas).
**Reemplaza:** borradores/f0_diseno.md (v1, con errores).

---

## 1. Objetivo de F0

F0 es alineacion contractual. No entrena, no interpreta, no verifica.
Prepara el terreno para que las fases siguientes sean medibles.

**Que certifica F0:**
- Coherencia de configuracion.
- Trazabilidad e inmutabilidad de la instancia de mision.
- Que banco, entrenador y acciones leen de la misma fuente.

**Que NO certifica F0:**
- Correccion nautica.
- Validez fisica.
- Que el barco llegue con v <= v_max (eso es evidencia dinamica, F3).
- Ninguna afirmacion de seguridad.

Esto va en el encabezado de cada manifiesto de corrida.

## 2. Instancia de mision (no config global)

La unidad es la **instancia de mision**, no un global mutable. Cada
contexto del banco lleva su propia `MisionConfig`, o una referencia
inequívoca a un perfil inmutable mas sus parametros especificos.

Asi coexisten T=10 y T=25 sin interferencia.

**Precision:** entrenador, simulador y acciones deben recibir la misma
instancia o una representacion equivalente con el mismo hash. No
basta con que cada modulo cargue por separado un perfil que podria
cambiar.

## 3. Estructura de la instancia

JSON plano, validado con JSON Schema. Sin lenguaje declarativo propio
en F0 (eso es del motor P-struct).




cat >> ~/navego_recuperado/timonel/borradores/f0_diseno_v2.md << 'EOF'

{
  "schema_version": "1.0",
  "mission_config_id": null,
  "mission_instance_hash": null,
  "goal": {
    "coordinates": {
      "x": {"valor": null, "unidad": "m", "procedencia": null, "estado": "sin_definir"},
      "z": {"valor": null, "unidad": "m", "procedencia": null, "estado": "sin_definir"},
      "sistema_referencia": {"valor": null, "procedencia": null, "estado": "sin_definir"}
    },
    "arrival_distance_threshold": {
      "valor": null, "unidad": "m", "operador": "<", "procedencia": null, "estado": "sin_definir"
    },
    "arrival_speed_limit": {
      "valor": null, "unidad": "kn", "operador": "<=", "procedencia": null, "estado": "sin_definir"
    }
  },
  "control": {
    "braking_target_speed": {
      "valor": null, "unidad": "kn", "procedencia": null, "estado": "sin_definir"
    }
  },
  "restricciones_duras": [],
  "limits": {
    "mission_time_limit_s": null,
    "limite_operativo_m": null
  },
  "outcomes": {
    "success_criteria": [],
    "abstention_conditions": "sin_definir",
    "all_actions_infeasible_policy": "sin_definir",
    "respuesta_seguridad": "sin_definir",
    "prioridad_exito_vs_restricciones": "sin_definir",
    "garantia_dinamica": "sin_evidencia",
    "justificacion": null
  }
}
Los `null` son marcadores de diseno, no valores ejecutables.

**Regla:** el cargador marca los valores no aprobados. El manifiesto
de cada experimento los lista.

## 4. Procedencia y estado

Cada valor lleva:
- `valor`: el numero o dato.
- `unidad`: m, kn, s, grados.
- `procedencia`: {heredado_codigo, experimento, director, normativa}.
- `estado`: {sin_definir, propuesto, aprobado_director}.

**Adicion de Luna:** registrar quien o que aprobo el valor y cuando.

**Adicion de Claude:** `normativa` debe incluir referencia
identificable a la fuente. No implica aplicabilidad legal automatica.
## 5. Invariantes y coherencia

**Invariante estatico (necesario, no suficiente):**
- `braking_target_speed <= arrival_speed_limit - margen`.
- `T > 0`.
- Velocidades >= 0.
- Coordenadas y sistema de referencia presentes.
- Limite operativo positivo.
- Validacion de tipos, unidades, rangos, campos obligatorios.
- Claves desconocidas dan error.

**Reserva critica (Luna + Claude):**
El invariante estatico evita el bloqueo "terminar nunca valida". NO
garantiza que el barco no supere v_max al cruzar T por inercia,
retardo o dinamica del controlador.

La garantia dinamica es un artefacto aparte:
- Mide velocidad al cruzar T en lazo cerrado.
- Sobre una grilla (v inicial, distancia, viento).
- Reporta peor caso y percentiles.
- Declara su envolvente.
- Atada a (hash de mision + version del simulador + ganancias del PID).

En la mision queda un campo `garantia_dinamica` con valor
`sin_evidencia` o el hash de la evidencia. Mientras diga
`sin_evidencia`, el manifiesto de cada corrida lo declara:
"invariante estatico OK; evidencia dinamica: ninguna".

## 6. Tres bloqueantes internos de F0

**Bloqueante 1: Funcion unica de etiquetado + regeneracion de bancos.**

Hoy el banco y el entrenador etiquetan por separado. Hay que unificar
en `etiquetar(mision, estado)` usada por banco, Entrenador y terminar.

Prueba de aceptacion: los bancos existentes (A2, probe, 0b) se
regeneran identicos desde sus configs. Para eso, un perfil retroactivo
por artefacto con procedencia `inferido_de_artefacto`, sin reescribir
el artefacto original.

**Bloqueante 2: Hash canonico con floats normalizados.**

`15` y `15.0` deben dar el mismo hash. Normalizar la representacion
(por ejemplo, cadenas decimales fijas).

**Bloqueante 3: Campo `garantia_dinamica` reservado.**

Debe existir en la estructura aunque valga `sin_evidencia`. Marca que
F0 cierra con la afirmacion "el barco llega con v <= v_max" declarada
como no respaldada.

## 7. Criterios de salida de F0

F0 esta completa cuando:

1. Existe el cargador unico `cargar_mision()` (inmutable).
2. Existe el JSON Schema con validacion.
3. Existe el hash canonico con floats normalizados.
4. Existe la funcion unica `etiquetar(mision, estado)`.
5. Los bancos A2, probe y 0b se regeneran identicos.
6. Existe el campo `garantia_dinamica` con valor `sin_evidencia`.
7. Existe el perfil `A2_legacy` con hash.
8. Existe el test guardian contra literales hardcodeados.
9. Los 6 desajustes del inventario estan resueltos o diferidos con
   justificacion.

**No bloquean F0:** evidencia dinamica, contenido de
`respuesta_seguridad`, `tiempo_maximo_mision`. F0 puede cerrar con
esos declarados como pendientes.

## 8. Lo que NO es F0

- No es entrenar.
- No es el interprete LLM.
- No es el verificador.
- No es la integracion.
- No certifica correccion nautica ni validez fisica.
