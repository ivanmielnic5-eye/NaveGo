# 13 — Mapas: DISCOVERY y CRITIQUE

## Fase 1 — DISCOVERY (GPT-4)

Pregunta: ¿Qué formato de mapas offline conviene para NaveGo?

Tres opciones evaluadas:
- MBTiles (contenedor SQLite de tiles, maduro, rígido)
- PMTiles (archivo único, acceso por rangos, spec v3 activa)
- GeoPackage (estándar OGC, SQLite general, rico semánticamente)

Hallazgo principal: NO son competidores equivalentes. Cumplen roles distintos.

Hipótesis emergente (NO decisión):
  Navigation Data  →  GeoPackage/SQLite
  Render Data      →  PMTiles o MBTiles

Justificación: coherencia con "Navigation Geometry ≠ Render Geometry".

Incógnitas declaradas: U-01 a U-06.

Estado: DISCOVERY COMPLETADO, DECISIÓN NO TOMADA.

## Fase 2 — CRITIQUE (Claude)

Veredictos sobre las afirmaciones del DISCOVERY:

- 1.1 Costo de runtime duplicado: MEJORABLE (ya cubierto por U-02).
- 1.2 No hay librería GeoPackage confirmada para RN/Expo: PELIGROSO
      (integración no verificada funcionando como supuesto resuelto).
- 2. Costo de mantener dos pipelines de ingesta: MEJORABLE.
- 3.1 Alternativa no evaluada: un solo archivo SQLite con tablas MBTiles
      + tablas propias de navegación.
- 3.2 FlatGeobuf: alternativa no evaluada para Navigation Data.
- 3.4 ¿Es necesaria la separación de formato? CUESTIONADA.
- 4.1 "PMTiles no soporta caching offline": CORRECTO (verificado con fuente).
- 4.2 "GeoPackage no se integra fácilmente con MapLibre RN": SUPUESTO
      (razonable, pero no declarado ni verificado).
- 4.3 "Navigation ≠ Render obliga a formatos distintos": SUPUESTO CRÍTICO
      (salto lógico no justificado).

Incógnitas nuevas declaradas por Claude: U-07 a U-10.

Incógnita más urgente según Claude: U-08
"¿La separación Navigation/Render puede lograrse con tablas o vistas
distintas dentro de un mismo archivo/formato, en vez de dos formatos?"

Si U-08 = SÍ → el resto del análisis cambia.
Si U-08 = NO → la hipótesis dual queda reforzada.

Estado: CRITIQUE COMPLETADO, DECISIÓN NO TOMADA.

## Próximo paso

Verificar U-08 antes de avanzar a DESIGN.
Hipótesis a testear: ¿un solo archivo SQLite puede contener:
  - tabla tiles + metadata (estándar MBTiles para render)
  - tabla navigation_features (propias para navegación)
Y consumirse desde MapLibre React Native sin requerir dos formatos?

## Fase 3 — Verificación de U-08 (GPT-4)

Pregunta: ¿Puede un único archivo SQLite contener simultáneamente
tablas estándar MBTiles (render) y tablas propias (navegación)?

### Hallazgos

MBTiles 1.3:
- NO prohíbe tablas adicionales.
- Requiere metadata + tiles.
- Admite estructuras internas adicionales.
- ADVIERTE: herramientas de terceros pueden no conservar tablas
  ajenas al esquema.

MapLibre:
- Admite MBTiles local (mbtiles://).
- Hay ejemplos reales en MapLibre RN.
- NO hay prueba documentada de MBTiles híbrido end-to-end.

expo-sqlite:
- Puede leer la misma tabla del mismo archivo.
- Es una tabla SQLite ordinaria.

Escritura:
- SQLite permite modificar.
- Pero mezclar ciclos de vida (tiles estáticos + datos dinámicos)
  es riesgo arquitectónico, no técnico.

### Resultado U-08

🟡 PARCIALMENTE CONFIRMADO

### Corrección importante al DISCOVERY original

"Navigation Geometry ≠ Render Geometry" NO implica
"Navigation Data ≠ Render File".

Son dos decisiones independientes.

### Dos arquitecturas posibles

A) UN ARCHIVO:
   region.mbtiles
   ├── metadata
   ├── tiles
   └── navigation_features

B) DOS ARCHIVOS (misma tecnología SQLite):
   render.mbtiles
   navigation.sqlite

### Pregunta para DESIGN

¿Qué arquitectura tiene menor coste total para NaveGo:
MBTiles híbrido o dos archivos SQLite especializados?

### Pendiente

Experimento mínimo: MapLibre RN + expo-sqlite sobre el mismo archivo.
Cerrar U-08b.

Estado: U-08 PARCIALMENTE CONFIRMADO. DECISIÓN ABIERTA.

## Fase 4 — DESIGN (GPT-4)

Pregunta: ¿Arquitectura un archivo híbrido (A) o dos archivos SQLite (B)?

### Análisis A (MBTiles híbrido)
- Técnicamente posible (spec MBTiles 1.3).
- Elegante: una región = un archivo.
- Riesgo: acopla ciclos de vida (tiles estáticos + navegación dinámica).
- Riesgo: herramientas de reempaquetado pueden no conservar tablas extra.
- NO demostrado: MapLibre + expo-sqlite sobre el mismo archivo.

### Análisis B (dos archivos SQLite)
- Separación limpia: render.mbtiles + navigation.sqlite.
- Ciclos de vida independientes.
- Actualizar mapa no toca datos de usuario.
- Pruebas independientes por subsistema.
- Coste: gestionar dos artefactos por región.

### Opción C (GeoPackage)
- Contenedor más expresivo.
- Integración directa con MapLibre RN no demostrada.

### Recomendación provisional (NO decisión)
B como candidato principal para prototipo.

Razón: reduce radio de fallo, desacopla ciclos de vida, permite verificar
cada subsistema independientemente (coherente con protocolo LOGOS).

### Incógnitas declaradas (U-08a a U-08f)
- U-08a: ¿MapLibre RN tolera MBTiles híbrido?
- U-08b: ¿MapLibre + expo-sqlite operan sobre el mismo archivo?
- U-08c: ¿Herramientas de generación conservan tablas adicionales?
- U-08d: ¿Impacto real de A vs B en RAM/CPU?
- U-08e: ¿Recuperación después de escritura interrumpida?
- U-08f: ¿Coste operativo de mantener dos archivos?

### Experimento mínimo propuesto (D-01)
1. Crear test-region/ con render.mbtiles + navigation.sqlite
2. MapLibre abre render.mbtiles
3. expo-sqlite abre navigation.sqlite
4. Insertar waypoint/hazard/restriction sin afectar render
5. Actualizar render.mbtiles sin tocar navigation.sqlite
6. Escritura abortada de navigation.sqlite → verificar recuperación
7. Repetir con A (test-hybrid.mbtiles)

### Métricas a registrar
Tiempo apertura, RAM pico, CPU, tiempo consulta, tiempo render,
tiempo zoom, tiempo pan, tiempo escritura, tiempo recuperación,
tamaño archivos, integridad post-interrupción.

### Estado
DESIGN: propuesta emitida.
DECISIÓN: ABIERTA.
IMPLEMENT: no autorizado todavía.

## Fase 5 — CRITIQUE del DESIGN (Claude)

### Objeciones contra B

- 1.1 Sincronización entre archivos no resuelta: PELIGROSO (sin incógnita asignada).
- 1.2 Atomicidad cruzada inexistente: MEJORABLE.
- 1.3 Distribución sin unidad atómica: PELIGROSO (sin incógnita asignada).
- 1.4 Versionado independiente: ventaja incompleta sin contrato de compatibilidad.

### Ventaja de A subestimada

La atomicidad transaccional nativa de un solo archivo resuelve 1.1 y 1.2
sin ingeniería adicional. También resuelve 1.3 por construcción.

### Arquitecturas D no consideradas

- D1: A, pero con el proceso de regeneración corregido
  (extraer navigation_features antes, reinsentar después).
- D2: B, pero empaquetado como unidad
  (directorio + manifest.json con region_id y checksums).

### Sobre el experimento D-01

Insuficiente. No prueba:
- Desincronización entre archivos (1.1).
- Si la herramienta real destruye tablas extra (asumido, no verificado).
- Acceso concurrente (MapLibre leyendo + sync escribiendo).
- En dispositivo real de gama media.

### Supuestos a verificar

- "Herramientas no conservan tablas extra": SUPUESTO. Verificable barato.
- "B reduce radio de fallo": cierto para corrupción aislada, NO para
  inconsistencia cruzada.
- "A y B pueden tener rendimiento similar": NO EXISTE en el DESIGN.
  Claude lo marcó por R-18. Error del prompt de auditoría.

### Riesgo de B no mencionado

Foreign keys de SQLite no funcionan entre archivos separados, ni
con ATTACH DATABASE. Las relaciones entre navigation.sqlite y
render.mbtiles quedan sin garantía a nivel de base de datos.

### Recomendación de Claude

Antes de correr D-01, cerrar U-consulta: ¿la herramienta real de
generación de tiles destruye tablas extra o no?
Es lo más barato de responder y sostiene toda la justificación de B.

## Fase 6 — Test experimental: tippecanoe vs tablas extra

Fecha: 2026-09-16
Objetivo: verificar el supuesto del DESIGN "herramientas de reempaquetado
pueden no conservar tablas extra".

Procedimiento:
1. Generar test.mbtiles con tippecanoe (1 feature, zoom 10-8).
2. Agregar tabla navigation_features (waypoint-1).
3. Verificar ANTES: tabla presente.
4. Regenerar test.mbtiles con tippecanoe --force.
5. Verificar DESPUÉS.

Resultado:
- ANTES: tabla presente con waypoint-1.
- DESPUÉS: "no such table: navigation_features".

Conclusión:
tippecanoe DESTRUYE las tablas extra al regenerar con --force.

Impacto:
- El supuesto central del DESIGN queda CONFIRMADO POR EVIDENCIA.
- A (archivo híbrido) queda comprometida si el workflow de regeneración
  usa tippecanoe.
- B (dos archivos) gana peso como arquitectura por defecto.

Pendiente:
- Probar D1 (A con proceso corregido: extraer tabla, regenerar, reinsertar).
- Probar A vs B en dispositivo real (TCL T610P).

Estado: evidencia obtenida. Decisión sigue abierta hasta probar D1.

## Fase 7 — Test D1: arquitectura A con proceso corregido

Fecha: 2026-09-16
Objetivo: verificar si A es viable si corregimos el proceso de regeneración.

Procedimiento:
1. Generar MBTiles con tippecanoe.
2. Agregar tabla navigation_features (waypoint-1).
3. Extraer tabla: sqlite3 .dump navigation_features > nav_dump.sql
4. Regenerar MBTiles con tippecanoe --force.
5. Reinsertar: sqlite3 test.mbtiles < nav_dump.sql
6. Verificar.

Resultado:
- ANTES: tabla presente con waypoint-1.
- DESPUÉS de regenerar+reinsertar: tabla presente con waypoint-1. ✅

Conclusión:
D1 FUNCIONA. A es viable con proceso corregido.
El problema no era de formato, era de proceso.

Impacto en la decisión A vs B:
- A ya NO está descartada.
- A requiere proceso especial (dump/reload antes de cada regeneración).
- B no requiere ese proceso, pero gestiona dos archivos.

Estado:
- A y B son técnicamente viables.
- La decisión ya NO es técnica.
- La decisión es de MANTENIMIENTO y RIESGO OPERACIONAL.

Comparación para decisión humana:

| Criterio | A (híbrido) | B (dos archivos) |
|----------|-------------|------------------|
| Archivos por región | 1 | 2 |
| Requiere dump/reload en cada regeneración | SÍ | NO |
| Riesgo de olvidar dump/reload | MEDIO | NINGUNO |
| Atomicidad transaccional | SÍ | NO (cruzada) |
| Sincronización de versiones | N/A | Requiere mecanismo |
| Distribución | 1 archivo | 2 archivos + manifiesto |
| Simplicidad de pipeline | Compleja (D1) | Simple |

Pendiente:
- Probar A y B en TCL T610P real (RAM/CPU/latencia).
- Decidir según criterios de mantenimiento.
