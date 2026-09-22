# DISEÑO — Agregar capas de texto al mapa

**Fecha:** 2026-09-22
**ID:** D-MAPAS-003
**Estado:** DISENO — pendiente critica GPT-4
**Autoridad final:** Ivan (Director Funcional)
**Antecedente:** El mapa se ve "minimalista" — sin nombres de ciudades,
rutas ni servicios. Los datos SI estan en el MBTiles, pero el estilo
no los dibuja.

---

## Diagnostico verificado

Estado actual del estilo en MapaOffline.tsx y MapaLocal.tsx:
- background  (fill de fondo)
- agua        (fill)
- edificios    (fill)
- lineas      (line)
- trackRefLine (line, azul, dash)
- trackActivoLine (line, rojo)

NINGUNA capa de tipo 'symbol'. Por eso no hay texto.

## Datos que SI existen en los MBTiles

Confirmado por decodificacion de un tile real:
- 'name'         → "Rosario", "Departamento San Lorenzo", "FC Belgrano", "Calle 4"
- 'name:es'      → nombres en español
- 'int_name'     → nombres internacionales
- 'ref'          → "RN9", "AP01", "CC"
- 'highway'      → "motorway", "primary", "residential", etc.
- 'place'        → (verificar si esta en todos los MBTiles)
- 'admin_level'  → "5", "9", "10" (departamentos, barrios)
- 'population'   → "193786"
- 'amenity'      → (verificar)

Verificado tambien que las coordenadas estan correctas
(lat negativa, hemisferio sur).

## Objetivo

Agregar 3 capas de tipo 'symbol' al estilo:
1. Ciudades y pueblos (siempre visibles).
2. Rutas nacionales (siempre visibles).
3. Servicios para viaje (a zoom alto).

## Alcance

- Modifica: components/MapaOffline.tsx y components/MapaLocal.tsx.
- NO modifica: MBTiles, config/mapas.ts, logica del server.
- NO regenera cartografia.

---

## Verificacion pendiente antes de implementar

Antes de escribir el codigo, hay que confirmar si 'place' y 'amenity'
estan realmente en los MBTiles. El filtro de DSH los incluyo, pero
no los vimos en el decode del tile de Rosario (z10).

Comando pendiente:
  Extraer un tile z12 de zona urbana (donde deberia haber ciudades
  y servicios) y verificar si 'place' y 'amenity' aparecen.

Si NO estan:
- Capa 1 (ciudades) se re-diseña con admin_level o boundary.
- Capa 3 (servicios) se descarta por ahora.

---

## Diseno de las 3 capas

### Capa 1 — Ciudades y pueblos

Proposito: saber donde estas. Rosario, San Nicolas, Zarate, etc.

Estructura conceptual (MapLibre):
  {
    id: 'ciudades',
    type: 'symbol',
    source: 'local',
    'source-layer': SOURCE_LAYER,
    filter: ['in', ['get', 'place'], ['literal', ['city','town','village']]],
    layout: {
      'text-field': ['coalesce', ['get','name:es'], ['get','name']],
      'text-size': ['case',
        ['==', ['get','place'], 'city'], 16,
        ['==', ['get','place'], 'town'], 13,
        11
      ],
      'text-anchor': 'top',
      'text-font': ['Open Sans Bold'],
    },
    paint: {
      'text-color': '#1a1a1a',
      'text-halo-color': '#ffffff',
      'text-halo-width': 2,
    }
  }

Notas:
- 'text-field' usa name:es si existe, sino name.
- Tamaño escalona por tipo (city > town > village).
- Halo blanco para que el texto se lea sobre cualquier fondo.
- Se dibuja DESPUES de las capas fill/line, para quedar arriba.

### Capa 2 — Rutas nacionales

Proposito: ver RN9, RN11, etc.

Estructura conceptual:
  {
    id: 'rutas',
    type: 'symbol',
    source: 'local',
    'source-layer': SOURCE_LAYER,
    filter: ['all',
      ['has', 'ref'],
      ['==', ['geometry-type'], 'LineString'],
      ['in', ['get', 'highway'], ['literal',
        ['motorway','trunk','primary','secondary']]]
    ],
    layout: {
      'text-field': ['get', 'ref'],
      'symbol-placement': 'line',
      'text-size': 11,
      'text-rotation-alignment': 'map',
      'text-font': ['Open Sans Regular'],
    },
    paint: {
      'text-color': '#7a5c00',
      'text-halo-color': '#ffffff',
      'text-halo-width': 1.5,
    }
  }

Notas:
- Se dibuja SOBRE la linea (symbol-placement: 'line').
- Solo motorway/trunk/primary/secondary, no calles menores.
- Color marron oscuro, halo blanco.

### Capa 3 — Servicios para viaje

Proposito: ver donde hay combustible, hospital, etc.

Estructura conceptual:
  {
    id: 'servicios',
    type: 'symbol',
    source: 'local',
    'source-layer': SOURCE_LAYER,
    filter: ['all',
      ['has', 'amenity'],
      ['in', ['get', 'amenity'], ['literal',
        ['fuel','hospital','clinic','pharmacy']]]
    ],
    minzoom: 12,
    layout: {
      'text-field': ['coalesce', ['get','name'], ''],
      'text-size': 10,
      'text-anchor': 'top',
      'text-font': ['Open Sans Regular'],
    },
    paint: {
      'text-color': '#b80000',
      'text-halo-color': '#ffffff',
      'text-halo-width': 1.5,
    }
  }

Notas:
- Aparece solo a partir de zoom 12 (calles y rutas visibles).
- No usa iconos por ahora (MapLibre con icono requiere imagenes).
  Solo texto con nombre. Es suficiente para la prueba del 29.
- Si 'amenity' no esta en los MBTiles, esta capa se omite.

### Orden de las capas en el array

El array 'layers' actual termina con:
  - trackRefLine
  - trackActivoLine

Se AGREGAN las 3 capas symbol DESPUES de todo lo demas, con este orden:
  background, agua, edificios, lineas,
  ciudades, rutas, servicios,
  trackRefLine, trackActivoLine

Motivo: los tracks (rojo/azul) deben quedar SIEMPRE visibles arriba
de todo lo demas, incluso los nombres. Asi el usuario no pierde su
linea roja bajo el texto.

---

## Verificacion previa obligatoria

Antes de escribir codigo hay que saber si 'place' y 'amenity' estan
en los MBTiles. Sin esa info, dos capas pueden quedar vacias.

Comando a ejecutar:

  Extraer un tile z12 de zona urbana y buscar los campos.

Si 'place' NO esta:
- Capa 1 (ciudades) se rediseña usando admin_level o boundary.

Si 'amenity' NO esta:
- Capa 3 (servicios) se descarta por ahora.

---

## Decisiones pendientes del Director

D-1: FUENTE DE LAS CIUDADES.
     Opciones si 'place' no existe:
     a) Usar admin_level=8 (municipio) + admin_level=7 (departamento).
     b) Usar admin_level=5 (departamento provincial).
     c) Descartar la capa de ciudades por ahora.
     Recomendacion: (a) si place falta.

D-2: FUENTE DE LOS SERVICIOS.
     Si 'amenity' no existe, ¿se reemplaza por otro campo o se
     descarta?
     Recomendacion: descartar. No tenemos certeza de que haya
     otra fuente confiable.

D-3: TAMAÑO DEL TEXTO.
     ¿Como se calcula el tamaño del texto de ciudades?
     a) Fijo 12px para todos.
     b) Escalona por tipo: city=16, town=13, village=11.
     Recomendacion: (b). Aprovechamos la info que ya viene en
     el MBTiles.

---

## Plan de implementacion (post-aprobacion)

Si el diseño se aprueba y la verificacion previa confirma los campos:

1. DSH prepara los 2 archivos refactorizados (Mision A).
2. Humano aplica (mismo metodo que Fase 1 de mapas).
3. Recompilar.
4. Verificar visualmente en el celu: nombres aparecen.
5. Si sale bien: commit.

Costo estimado: 30-40 minutos entre todos los pasos.

---

## Preguntas para GPT-4

P-1: ¿La prioridad de las capas es correcta?
P-2: ¿El orden (tracks arriba de los simbolos) es correcto?
P-3: ¿El uso de name:es antes que name es correcto?
P-4: ¿Falta alguna capa util (por ejemplo, aeropuertos, puertos)?
P-5: ¿Es sobrearquitectura agregar 3 capas ahora, o conviene
     menos?
P-6: ¿Hay alguna optimizacion de performance para gama baja?

La decision final es del Director.

---
Fin del diseño.

---

## AJUSTE — Hallazgos de la verificacion previa

La verificacion previa (tiles z10 y z12 de Rosario) revelo:

### place NO sirve como fuente

'place=city' y 'place=town' NO estan en los MBTiles.
Solo hay: neighbourhood, suburb, region, islet, island.

-> La Capa 1 no puede usar 'place'. Se rediseña con admin_level.

### admin_level SI sirve

Valores observados en tiles reales:
- admin_level=4  -> provincia (Rio Parana)
- admin_level=5  -> departamento (Departamento San Lorenzo)
- admin_level=6  -> aglomerado (Gran Rosario)
- admin_level=7  -> municipio grande (Municipio de Funes)
- admin_level=8  -> municipio chico (Ybarlucea)
- admin_level=9  -> barrio/parque (Quinta Natacha)
- admin_level=10 -> barrio chico (Lago Sereno)
- admin_level=11 -> sub-barrio (Barrio del Golf)

### amenity SI sirve

Valores observados:
- fuel, hospital, clinic, pharmacy, police, cafe, restaurant,
  fast_food, bank, parking, toilets, marketplace, bicycle_parking,
  motorcycle_parking, ice_cream, weighbridge, clock

-> La Capa 3 va tal cual estaba disenada.

### Decision del Director sobre barrios

Decision tomada: SI mostrar barrios (admin_level 9, 10, 11).
Con minzoom: 12 (aparecen solo a nivel calle).

---

## Diseno REVISADO de la Capa 1 — Municipios y barrios

Se divide en DOS sub-capas, con zoom distinto:

### Capa 1a — Municipios y aglomerados (siempre visible)

  {
    id: 'municipios',
    type: 'symbol',
    source: 'local',
    'source-layer': SOURCE_LAYER,
    filter: ['all',
      ['has', 'admin_level'],
      ['in', ['get', 'admin_level'],
        ['literal', ['5','6','7','8']]],
      ['has', 'name']
    ],
    layout: {
      'text-field': ['coalesce', ['get','name:es'], ['get','name']],
      'text-size': ['case',
        ['==', ['get','admin_level'], '5'], 15,
        ['==', ['get','admin_level'], '6'], 14,
        ['==', ['get','admin_level'], '7'], 13,
        11
      ],
      'text-anchor': 'center',
      'text-font': ['Open Sans Bold'],
    },
    paint: {
      'text-color': '#1a1a1a',
      'text-halo-color': '#ffffff',
      'text-halo-width': 2,
    }
  }

Notas:
- Administrativo provincial (5), aglomerado (6), municipio (7, 8).
- Tamano escalona por nivel.
- Visible en todos los zooms.

### Capa 1b — Barrios (zoom alto)

  {
    id: 'barrios',
    type: 'symbol',
    source: 'local',
    'source-layer': SOURCE_LAYER,
    minzoom: 12,
    filter: ['all',
      ['has', 'admin_level'],
      ['in', ['get', 'admin_level'],
        ['literal', ['9','10','11']]],
      ['has', 'name']
    ],
    layout: {
      'text-field': ['coalesce', ['get','name:es'], ['get','name']],
      'text-size': 10,
      'text-anchor': 'center',
      'text-font': ['Open Sans Regular'],
    },
    paint: {
      'text-color': '#404040',
      'text-halo-color': '#ffffff',
      'text-halo-width': 1.5,
    }
  }

Notas:
- Solo aparece a zoom 12+ (nivel calle).
- Texto mas chico, color gris oscuro.
- Menos prominente que los municipios.

---

## Orden final de las capas

Array 'layers' de MapLibre, de abajo hacia arriba:

  1. background
  2. agua
  3. edificios
  4. lineas
  5. municipios      (nuevo — siempre visible)
  6. barrios         (nuevo — z12+)
  7. rutas           (nuevo — siempre visible)
  8. servicios       (nuevo — z12+)
  9. trackRefLine
  10. trackActivoLine

Motivo: los tracks (rojo/azul) quedan SIEMPRE arriba.
Las capas de texto van antes que los tracks.

---

## Decisiones aplicadas al diseno revisado

- D-1: RESUELTO — Se usa admin_level, no place.
- D-2: RESUELTO — amenity existe, capa 3 va tal cual.
- D-3: RESUELTO — Tamano escalona por tipo.
- D-4 (nuevo, del Director): Barrios SI. Capa 1b con minzoom 12.

---

## Plan de implementacion (post-aprobacion)

Total: 4 capas symbol (municipios, barrios, rutas, servicios).

1. DSH prepara los 2 archivos refactorizados (Mision A).
2. Humano aplica (mismo metodo que Fase 1 de mapas).
3. Recompilar.
4. Verificar visualmente en el celu: nombres aparecen.
5. Si sale bien: commit.

---

## Preguntas revisadas para GPT-4

P-1: La division en municipios + barrios es correcta, o conviene
     una sola capa con zoom variable?
P-2: El tamano del texto es adecuado para TCL T610P (gama media)?
P-3: La prioridad y el orden de las capas es correcta?
P-4: Falta alguna capa util (por ejemplo, aeropuertos, puertos)?
P-5: Hay sobrearquitectura en agregar 4 capas ahora?
P-6: Hay alguna optimizacion de performance para gama baja
     (muchas features de texto a zoom alto)?
P-7: El uso de name:es antes que name es correcto?
P-8: Hay algun riesgo de que el texto invada el track rojo?

La decision final es del Director.

---
Fin del diseno revisado.
