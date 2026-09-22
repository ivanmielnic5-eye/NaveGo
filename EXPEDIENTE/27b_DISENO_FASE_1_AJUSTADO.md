# DISEÑO Fase 1 (AJUSTADO) — desacoplar app de un solo mapa

**Fecha:** 2026-09-22
**ID:** D-MAPAS-002 (reemplaza D-MAPAS-001)
**Estado:** DISEÑO AJUSTADO — pendiente aprobacion Director
**Autoridad final:** Ivan (Director Funcional)

---

## Por que este ajuste

La version anterior (D-MAPAS-001) fue revisada por Claude (critica
arquitectonica del 2026-09-22). Claude acepto el diseno como
respetuoso de la advertencia "no portabilidad prematura", pero
senalo 4 mejoras. Se incorporan.

## Cambios respecto a D-MAPAS-001

CAMBIO 1 (Claude C-2, importante): namespacing de URL del servidor.

Problema detectado: hoy el servidor embebido sirve tiles en
  /{z}/{x}/{y}.pbf
sin identificar de que mapa son. Si MapLibre tiene cache de un tile
de santa_fe y luego el mapa activo cambia a corredor_sf_caba, el
mismo path devuelve el tile cacheado viejo. Eso produce mezcla de
tiles de dos mapas sin error visible.

Solucion: namespacing por id de mapa.
  /{mapaId}/{z}/{x}/{y}.pbf
Ejemplo:
  /santa_fe/10/339/606.pbf
  /corredor_sf_caba/10/339/606.pbf
El servidor lee el mapaId del path y sirve del mapa correspondiente.
Esto ademas prepara el terreno para Fase 2 (varios mapas activos).

CAMBIO 2 (Claude C-3): de 3 archivos a 2.

La version previa tenia:
  config/mapas.json
  config/mapas-registry.ts
  config/mapas.ts

Claude: la separacion JSON/TS solo tiene sentido cuando el catalogo
es remoto (no bundleado). Fase 1 no lo es. Se unifica en UN archivo:
  config/mapas.ts

CAMBIO 3 (Claude, PUERTO): sacar duplicacion del PUERTO.
El PUERTO=8080 estaba declarado en cada componente. Se mueve a
config/mapas.ts (o un config compartido). Un solo lugar.

CAMBIO 4 (Claude C-6): agregar campo version al descriptor.
Cada descriptor de mapa lleva un campo "version" (o fecha de
generacion). Motivo: si el corredor se regenera antes del 29 sep,
la app puede decir cual version esta viendo. Es un dato de
procedencia, alineado con el patron de LOGOS (context_revision,
git_commit).

CAMBIO 5 (Claude C-5): mapa activo como ESTADO, no constante.
Hoy el diseno decia que "activo" se lee de un archivo fijo. Claude
sugiere: el mapa activo debe ser estado de runtime (aunque hoy
nada lo cambie). Asi, cuando en Fase 2 se cablee un boton para
cambiar de mapa, es conectar una funcion existente, no redisenar
la forma del estado.

---

---

## Contrato ajustado del descriptor

Un solo archivo: config/mapas.ts. Contiene:

1) El tipo MapDescriptor.
2) El catalogo de mapas (hardcodeado en el TS).
3) El registry de assets (require literales).
4) El estado del mapa activo (variable de modulo).
5) Funciones: getMapaActivo(), setMapaActivo(id), MAPAS.

Estructura conceptual:

  // config/mapas.ts

  export const PUERTO = 8080;

  export type MapDescriptor = {
    id: string;
    nombre: string;
    archivo: string;          // nombre del mbtiles
    sourceLayer: string;
    center: [number, number];
    minzoom: number;
    maxzoom: number;
    version: string;          // NUEVO (Claude C-6)
    asset: any;               // require literal
  };

  const CATALOGO: Record<string, MapDescriptor> = {
    santa_fe: {
      id: 'santa_fe',
      nombre: 'Santa Fe (provincia)',
      archivo: 'santa_fe.mbtiles',
      sourceLayer: 'santa_fe',
      center: [-60.7, -31.63],
      minzoom: 8,
      maxzoom: 14,
      version: '2026-09-20',
      asset: require('../assets/maptest/santa_fe.mbtiles'),
    },
    corredor_sf_caba: {
      id: 'corredor_sf_caba',
      nombre: 'Corredor Santa Fe - CABA (RN9)',
      archivo: 'corredor_sf_caba.mbtiles',
      sourceLayer: 'corredor',
      center: [-60.7, -31.63],     // <- DECISION D-1 pendiente
      minzoom: 8,
      maxzoom: 14,
      version: '2026-09-22',
      asset: require('../assets/maptest/corredor_sf_caba.mbtiles'),
    },
  };

  // Estado del mapa activo (Claude C-5)
  let mapaActivoId: string = 'santa_fe';  // <- DECISION D-2 pendiente

  export function getMapaActivo(): MapDescriptor {
    const m = CATALOGO[mapaActivoId];
    if (!m) throw new Error(
      'Mapa activo invalido: ' + mapaActivoId +
      '. Mapas disponibles: ' + Object.keys(CATALOGO).join(', ')
    );
    return m;
  }

  export function setMapaActivo(id: string): void {
    if (!CATALOGO[id]) throw new Error('Mapa no encontrado: ' + id);
    mapaActivoId = id;
  }

  export function getMapasDisponibles(): string[] {
    return Object.keys(CATALOGO);
  }

Notas:
- El require sigue siendo literal (Metro lo exige). Pero vive
  UNA SOLA VEZ, aca. Los componentes ya no tienen require.
- El error de mapa invalido es explicito y enumera los validos.
  Cumple con el criterio de test negativo (C-11).

---

## Flujo actualizado (con URL namespacing)

  1. App arranca. getMapaActivo() devuelve descriptor + asset.
  2. Copia asset a documentDirectory (mismo flujo que hoy).
  3. Abre SQLite sobre el archivo copiado.
  4. Inicia servidor HTTP.
  5. Servidor sirve URLs namespaced:
       /{mapaId}/{z}/{x}/{y}.pbf
     Ejemplo:
       /santa_fe/10/339/606.pbf
     El server valida que mapaId == mapaActivoId (o sirve de la DB
     que ya tiene cargada).
  6. MapLibre consume:
       http://127.0.0.1:8080/{mapaId}/{z}/{x}/{y}.pbf
     El estilo incluye el mapaId real, no un placeholder.
  7. Cache de MapLibre ya no puede mezclar: los paths son distintos
     por mapa.

---

## Que sale de cada componente

MapaOffline.tsx y MapaLocal.tsx:

SALE (ya no se declara en el componente):
  const DB_NAME = 'santa_fe.mbtiles';
  const SOURCE_LAYER = 'santa_fe';
  const CENTER_DEFAULT = [-60.7, -31.63];
  const PUERTO = 8080;                      // se importa de config
  require('../assets/maptest/santa_fe.mbtiles')

ENTRA:
  import { getMapaActivo, PUERTO } from '../config/mapas';

  const mapa = getMapaActivo();
  const DB_NAME = mapa.archivo;
  const DB_PATH = DIR + DB_NAME;
  const SOURCE_LAYER = mapa.sourceLayer;
  const CENTER_DEFAULT = mapa.center;
  const MINZOOM = mapa.minzoom;
  const MAXZOOM = mapa.maxzoom;

SE MANTIENE (no cambia):
  const DIR = FileSystem.documentDirectory + 'maptest/';
  Toda la logica de copiar asset, abrir SQLite, montar el server,
  los useEffect de ubicacion, el aGeoJSON, el estilo de MapLibre.

CAMBIA el patron de URL del server:
  antes: path.match(/^\/(\d+)\/(\d+)\/(\d+)\.pbf$/)
  ahora: path.match(/^\/([^\/]+)\/(\d+)\/(\d+)\/(\d+)\.pbf$/)
         donde el primer grupo es mapaId.

CAMBIA la URL que se pasa a MapLibre:
  antes: http://127.0.0.1:8080/{z}/{x}/{y}.pbf
  ahora: http://127.0.0.1:8080/{mapaId}/{z}/{x}/{y}.pbf
         con {mapaId} ya resuelto al id real del descriptor.

---

---

## Criterios de aceptacion (verificacion)

Mismos que D-MAPAS-001, MAS los criterios nuevos que agrega el
namespacing y el estado de mapa activo:

1. App arranca con el mapa por defecto configurado.
2. Tracker sigue dibujando la linea roja.
3. Sin errores en log de arranque ([ML] 1-5 OK).
4. Sin require() dinamico. Solo registry estatico.
5. Id inexistente produce error claro con lista de validos.

Nuevos (post-Claude):

6. Verificar que el server sirve URLs namespaced:
   - Probar en el celu: http://127.0.0.1:8080/santa_fe/10/339/606.pbf
     -> devuelve tile de Santa Fe.
   - Probar: http://127.0.0.1:8080/corredor_sf_caba/10/339/606.pbf
     -> devuelve tile del corredor, DISTINTO al anterior.
   - Esto confirma que el namespacing evita la mezcla de cache.

7. Verificar cambio de mapa activo en caliente:
   - setMapaActivo('corredor_sf_caba') debe permitir cambiar
     sin reiniciar el server (o reiniciarlo explicitamente).
   - Documentar el comportamiento (cambio en caliente o
     requiere remount).

8. Verificar version en el descriptor:
   - getMapaActivo().version devuelve el string configurado.
   - Util para diagnostico: "que version del mapa estoy viendo".

---

## Plan de desembarco (con rollback por paso)

**Regla del desembarco cauteloso:** cada paso se verifica antes de
pasar al siguiente. Si algo falla -> rollback del paso, no del todo.

### Preparacion (10 min)

P0. Backup del working tree actual:
    git status -> debe estar limpio. Si no, commit primero.
    git log -1 -> guardar hash actual (punto de rollback global).
    git tag pre-fase1-mapas -> marca el punto de partida.

### Paso 1 — Crear config/mapas.ts (no toca nada existente)

Escribir el archivo config/mapas.ts con:
- Tipo MapDescriptor.
- CATALOGO con santa_fe y corredor_sf_caba.
- mapaActivoId = 'santa_fe' (default seguro = comportamiento actual).
- Funciones getMapaActivo, setMapaActivo, getMapasDisponibles.
- PUERTO exportado.

VERIFICACION: tsc --noEmit (no debe dar error).

ROLLBACK: rm config/mapas.ts. Nada mas se toco.

### Paso 2 — Modificar MapaOffline.tsx (un solo archivo)

Cambios:
- Import de config/mapas.
- Reemplazar hardcodes por llamada a getMapaActivo().
- Cambiar regex del server para aceptar {mapaId}.
- Cambiar URL que se pasa a MapLibre.

VERIFICACION:
- tsc --noEmit (sin errores).
- Recompilar APK. Verificar que arranca con santa_fe igual que hoy.
- Log [ML] 1-5 OK.

ROLLBACK: git checkout components/MapaOffline.tsx.
Solo se revierte ese archivo.

### Paso 3 — Modificar MapaLocal.tsx (mismo patron)

Cambios analogos a paso 2. Respetar que MapaLocal tiene codigo de
ubicacion que MapaOffline no tiene.

VERIFICACION: tsc + APK + verificar que la pantalla donde vive
MapaLocal sigue funcionando.

ROLLBACK: git checkout components/MapaLocal.tsx.

### Paso 4 — Probar cambio de mapa activo

Editar config/mapas.ts: mapaActivoId = 'corredor_sf_caba'.
Recompilar. Abrir la app. Verificar:
- El mapa del corredor se dibuja.
- El tracker sigue dibujando encima.
- No hay errores.

VERIFICACION FISICA: mover el mapa hasta una zona conocida del
corredor (Rosario, por ejemplo) y ver que los tiles son coherentes
(sin mezcla con Santa Fe).

ROLLBACK: volver mapaActivoId a 'santa_fe'. Recompilar.

### Paso 5 — Test negativo

Editar config/mapas.ts: mapaActivoId = 'no_existe'.
Recompilar. Abrir la app. Verificar:
- La app NO crashea silenciosamente.
- Muestra error claro (o falla con mensaje legible).

ROLLBACK: volver mapaActivoId a 'santa_fe'.

### Commit final

Si los 5 pasos pasan: commit con todos los archivos.
Si un paso falla: rollback de ese paso, avisar, NO avanzar.

---

## Decisiones pendientes del Director

D-1: Center del descriptor del corredor.
     Opciones:
     a) [-60.7, -31.63] — mismo que Santa Fe (cerca de la capital).
     b) [-60.65, -32.95] — cerca de Rosario (punto medio del corredor).
     c) [-58.4, -34.6]  — cerca de CABA (destino del viaje).
     Recomendacion de la IA: (b) Rosario. Es el punto medio real del
     corredor, la app abre donde estas viajando.

D-2: Mapa activo por defecto.
     Opciones:
     a) 'santa_fe' — comportamiento actual intacto. Mas seguro.
     b) 'corredor_sf_caba' — la app arranca con el mapa del viaje.
        Menos seguro: si algo sale mal, afecta el viaje.
     Recomendacion: empezar con (a), cambiar a (b) solo para el viaje
     del 29. Asi el refactor se prueba primero con el mapa conocido.

D-3: Rol de DSH en la implementacion.
     Claude sugirio: NO pasarsela a DSH todavia, cerrar primero
     C-2 (namespacing) y C-6 (version). Ambos ya estan cerrados en
     este diseno. Con eso cerrado, DSH puede preparar los cambios.
     Opciones:
     a) DSH prepara los 2 archivos, humano aplica y verifica.
     b) Humano + IA aplican directo (sin DSH). Mas rapido pero menos
        aprendizaje para DSH.
     c) DSH prepara Y aplica (Mision A + B), humano verifica.
     Recomendacion: (a). DSH prepara, humano aplica. Es la primera
     mision de refactor de DSH; empecemos conservadores.

---

## Fin del diseno Fase 1 ajustado.

Proximo paso cuando el Director apruebe:
1. Confirmar D-1, D-2, D-3.
2. Armar Mision A para DSH (si D-3 = a).
3. Ejecutar plan de desembarco paso a paso.
