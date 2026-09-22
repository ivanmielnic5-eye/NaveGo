# DISEÑO — Fase 1: desacoplar la app de un solo mapa

**Fecha:** 2026-09-22
**ID:** D-MAPAS-001
**Estado:** DISEÑO — pendiente crítica GPT-4
**Autoridad final:** Iván (Director Funcional)
**Objetivo:** incorporar el corredor SF->CABA antes del 29 sep
sin construir todavía una biblioteca completa.

---

## Advertencia que se respeta

Claude, el 14 sep 2026:
- "No diseñar portabilidad antes de tener una app funcionando."
- "No elegir formato de mapa (MBTiles/PMTiles/GeoPackage) sin
  medirlo en un caso de uso real."

Este diseño NO crea portabilidad. Solo saca el hardcodeo de un
solo mapa. La biblioteca completa es Fase 2.

---

## Estado actual verificado (2026-09-22)

### Consumidores

Dos componentes cargan mapas, cada uno con el mismo bloque copiado:

- components/MapaOffline.tsx (169 lineas) — HUD principal.
- components/MapaLocal.tsx — componente secundario.

Ambos tienen:

  const DB_NAME = 'santa_fe.mbtiles';
  const DB_PATH = DIR + DB_NAME;
  const PUERTO = 8080;
  const SOURCE_LAYER = 'santa_fe';
  const CENTER_DEFAULT = [-60.7, -31.63];
  require('../assets/maptest/santa_fe.mbtiles')  // literal

### Servidor HTTP embebido

La app corre react-native-nitro-http-server en puerto 8080.
Es 100% local (127.0.0.1, dentro del celu).
NO tiene relacion con el navego-bridge.service de la mini PC
(que fue apagado hoy).

### Assets actuales en assets/maptest/

| Archivo                  | Tamano | source_layer | minzoom | maxzoom |
|--------------------------|--------|--------------|---------|---------|
| santa_fe.mbtiles         | 122 MB | santa_fe     | 8       | 14      |
| corredor_sf_caba.mbtiles | 100 MB | corredor     | 8       | 14      |
| render_big.mbtiles       | 42 MB  | tucuman      | 8       | 14      |
| render.mbtiles           | 36 KB  | puntos       | 8       | 12      |
| test_hibrido.mbtiles     | 40 KB  | puntos       | 8       | 12      |
| navigation.sqlite        | 8 KB   | —            | —       | —       |

### navigation.sqlite

Solo lo carga components/TestMapLibre.tsx (componente de test).
Produccion (MapaOffline/MapaLocal) NO lo usa. Es residuo.

### Restriccion de Metro/Expo

require() en React Native DEBE recibir un string literal.
No se puede hacer require(rutaVariable). Necesita registry estatico.

---

## Contrato minimo del descriptor

Un archivo `mapas.json` en la raiz de assets/maptest/ o en /config/.
Estructura:

  {
    "activo": "santa_fe",
    "mapas": {
      "santa_fe": {
        "id": "santa_fe",
        "nombre": "Santa Fe (provincia)",
        "archivo": "santa_fe.mbtiles",
        "sourceLayer": "santa_fe",
        "center": [-60.7, -31.63],
        "minzoom": 8,
        "maxzoom": 14
      },
      "corredor_sf_caba": {
        "id": "corredor_sf_caba",
        "nombre": "Corredor Santa Fe - CABA (RN9)",
        "archivo": "corredor_sf_caba.mbtiles",
        "sourceLayer": "corredor",
        "center": [-60.7, -31.63],
        "minzoom": 8,
        "maxzoom": 14
      }
    }
  }

Solo estos campos. Ninguno mas en Fase 1.
- id: identificador logico.
- nombre: para mostrar al humano (no usado en Fase 1 todavia).
- archivo: nombre del MBTiles.
- sourceLayer: la capa vectorial dentro del MBTiles.
- center: centro geografico por defecto.
- minzoom/maxzoom: limites de zoom.

NO incluir todavia: version, hash, bounds, descripcion, fecha,
proveedor, licencia, tamaño, region, categoria, tags.
Eso es Fase 2.

---

## Registry estatico de assets (obligatorio por Metro)

Un archivo `mapas-registry.ts` (o .js) que traduce el id logico
a un require literal. Metro NO permite require(rutaVariable).

  export const MAPAS_REGISTRY: Record<string, any> = {
    'santa_fe':        require('../assets/maptest/santa_fe.mbtiles'),
    'corredor_sf_caba': require('../assets/maptest/corredor_sf_caba.mbtiles'),
  };

Es el unico lugar del codigo donde aparecen require() literales.

---

## Como se usa (flujo)

  1. App arranca.
  2. Lee mapas.json.
  3. Toma el id de "activo".
  4. Busca el descriptor del mapa activo.
  5. Busca el require correspondiente en MAPAS_REGISTRY.
  6. Usa el sourceLayer, center, minzoom, maxzoom del descriptor
     para armar el estilo de MapLibre.
  7. Corre el servidor HTTP embebido como hoy.

El componente NO sabe el nombre del archivo. Solo recibe un id.
El descriptor dice el resto.

---

## Que sale de MapaOffline.tsx y MapaLocal.tsx

Se ELIMINAN las constantes hardcodeadas:

  const DB_NAME = 'santa_fe.mbtiles';       -> viene del descriptor
  const DB_PATH = DIR + DB_NAME;            -> se calcula en runtime
  const PUERTO = 8080;                      -> se queda (es fijo del celu)
  const SOURCE_LAYER = 'santa_fe';          -> viene del descriptor
  const CENTER_DEFAULT = [-60.7, -31.63];   -> viene del descriptor
  require('../assets/maptest/santa_fe...')  -> viene del registry

Quedan como constantes del componente (no cambian entre mapas):

  const DIR = FileSystem.documentDirectory + 'maptest/';
  const PUERTO = 8080;

Se agrega un import:

  import { getMapaActivo } from '../config/mapas';
  // o la ruta que corresponda

Se reemplaza:

  const DB_NAME = 'santa_fe.mbtiles';
  const DB_PATH = DIR + DB_NAME;
  const SOURCE_LAYER = 'santa_fe';
  const CENTER_DEFAULT: [number, number] = [-60.7, -31.63];

por algo como:

  const mapa = getMapaActivo();  // lee mapas.json + registry
  const DB_NAME = mapa.archivo;
  const DB_PATH = DIR + DB_NAME;
  const SOURCE_LAYER = mapa.sourceLayer;
  const CENTER_DEFAULT: [number, number] = mapa.center;

Y en el useEffect, reemplazar:

  require('../assets/maptest/santa_fe.mbtiles')

por:

  mapa.asset  // el require viene del registry

---

## Que NO se toca en Fase 1

- El servidor HTTP embebido (nitro-http-server, puerto 8080).
- El flujo de copiado de asset a documentDirectory.
- El estilo de MapLibre (colores, capas, orden).
- Los otros componentes (App.tsx, HUD, tracker).
- navigation.sqlite (residuo, no se usa en produccion).
- El formato MBTiles (no se cambia a PMTiles/GeoPackage).
- El empaquetado del APK (los 2 MBTiles siguen viajando adentro).
- El .gitignore (los MBTiles quedan en assets, van al APK).

---

## Criterios de aceptacion (como verificar que funciona)

Un cambio de Fase 1 se considera BIEN implementado si cumple TODO esto:

1. La app arranca con el mapa santa_fe (comportamiento actual intacto).
2. Se edita mapas.json: "activo": "corredor_sf_caba".
3. Se recompila.
4. La app arranca con el corredor SF->CABA dibujado.
5. Al rotar, zoom, mover: el mapa responde igual que antes.
6. El tracker sigue dibujando la linea roja sobre el nuevo mapa.
7. No hay errores en el log de arranque ([ML] 1-5 OK).
8. MapaLocal.tsx tambien respeta el cambio.
9. Ningun require() dinamico. Solo registry estatico.
10. Cambiar "activo" a un id inexistente produce error claro
    (no un crash silencioso).

Test negativo (importante):
11. Si "activo" apunta a un id que no existe en el registry,
    la app debe mostrar un error explicito, no quedar en blanco.

---

## Riesgos e incertidumbres

R-1: El centro por defecto de Santa Fe no coincide con el corredor.
     Cuando el mapa activo sea corredor, el centro geografico
     deberia ser distinto (por ejemplo, cerca de Rosario, punto
     medio del corredor).
     -> Decision humana: ¿que center poner en el descriptor del
     corredor?

R-2: El corredor tiene bounds mas anchos que la zona de Santa Fe.
     Eso significa que si el usuario zoomea fuera del corredor,
     no vera mapa (porque no hay tiles).
     -> Aceptable para el viaje. Documentar.

R-3: El style de MapLibre tiene lineas duras: 'line-color',
     'line-width' fijos. No cambian por mapa. Si en el futuro
     otro mapa necesita otro estilo, habria que mover eso tambien
     al descriptor. NO en Fase 1.

R-4: El require() estatico obliga a que cada MBTiles este en el
     APK. Con 2 mapas sumamos ~222 MB al APK. Si sumamos mas
     regiones, el APK se vuelve inmanejable. Eso es problema de
     Fase 2 (provisionamiento externo).

R-5: MapaLocal.tsx tiene codigo de ubicacion (Location.request...)
     que MapaOffline.tsx no tiene. Cualquier refactor tiene que
     respetar esa diferencia.

R-6: No verificado: si el MBTiles del corredor funciona 100% en
     el celu con la misma performance que santa_fe. Se va a
     verificar con la prueba del 29 sep.

---

## Plan de implementacion (cuando se apruebe)

Fase 1 (1-2 horas de trabajo, sin apuro):

1. Crear config/mapas.json con los 2 descriptores.
2. Crear config/mapas-registry.ts con los 2 require literales.
3. Crear config/mapas.ts con getMapaActivo() que:
   - Lee mapas.json
   - Devuelve el descriptor + el require correspondiente
4. Modificar components/MapaOffline.tsx: usar getMapaActivo().
5. Modificar components/MapaLocal.tsx: idem.
6. Verificar: recompilar y probar con santa_fe (default).
7. Verificar: cambiar "activo" a corredor_sf_caba, recompilar,
   probar.
8. Si funciona: commit.
9. Si no: revertir (son dos archivos, trivial).

NO incluye:
- UI de seleccion.
- Descarga de mapas.
- Editor de mapas.json desde la app.
- Sincronizacion.
- Ningun tipo de catalogo remoto.

---

## Preguntas pendientes para critica GPT-4

P-1: ¿El contrato minimo es suficiente, o falta algo?
P-2: ¿La separacion mapas.json / registry / mapas.ts es correcta?
P-3: ¿El estilo de MapLibre deberia ir al descriptor tambien?
P-4: ¿Que center deberia tener el descriptor del corredor?
P-5: ¿Hay algun riesgo adicional que no vi?
P-6: ¿La Fase 1 respeta la advertencia de Claude?
P-7: ¿Que parte del futuro Map Region Package conviene NO
     anticipar ahora?
P-8: ¿Que parte minima SI conviene dejar preparada ahora?

La decision final es del Director.

---
Fin del diseno Fase 1.
