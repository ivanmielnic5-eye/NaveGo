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
