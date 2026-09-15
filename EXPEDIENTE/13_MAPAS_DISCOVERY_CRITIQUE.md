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
