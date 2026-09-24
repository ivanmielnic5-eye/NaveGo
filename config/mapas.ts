// config/mapas.ts — ARCHIVO NUEVO (Fase 1: desacoplar la app de un solo mapa)
//
// FUENTE DE DISENO: EXPEDIENTE/27b_DISENO_FASE_1_AJUSTADO.md (D-MAPAS-002)
// Decisiones del Director aplicadas:
//   D-1 = (b) center del corredor = [-60.65, -32.95]  (Rosario, punto medio)
//   D-2 = (a) mapa activo por defecto = "santa_fe"    (comportamiento actual intacto)
//   D-3 = (a) DSH prepara, humano aplica
//
// ESTE ARCHIVO NO ESTA APLICADO AL REPO. Vive en el sandbox.
//
// NOTA DE UBICACION (ver REVIEW.md, seccion Incertidumbres):
//   El diseno 27b asume que el asset del corredor vive en
//   assets/maptest/corredor_sf_caba.mbtiles.
//   Verificado el 2026-09-22: ese archivo NO existe todavia.
//   El .mbtiles del corredor esta en sandbox_corredor/out_mision_b/.
//   El require de abajo apunta a la ruta objetivo del diseno. Requiere
//   que el humano copie el asset antes de aplicar (ver REVIEW.md).

export const PUERTO = 8080;

export type MapDescriptor = {
  id: string;
  nombre: string;
  archivo: string; // nombre del mbtiles
  sourceLayer: string;
  sourceLayerAdmin?: string;
  sourceLayerAdminPais?: string;
  center: [number, number];
  minzoom: number;
  maxzoom: number;
  version: string; // procedencia (Claude C-6)
  asset: any; // require literal (Metro exige literal, no variable)
};

// Catalogo de mapas disponibles.
// El require DEBE ser literal: Metro no resuelve require(variable).
// Por eso vive UNA SOLA VEZ aca; los componentes ya no tienen require.
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
    archivo: 'corredor_sf_caba_z5.mbtiles',
    sourceLayer: 'corredor',
    sourceLayerAdmin: 'admin',
    sourceLayerAdminPais: 'admin_pais',
    center: [-60.65, -32.95], // D-1 = (b) Rosario, punto medio
    minzoom: 5,
    maxzoom: 14,
    version: '2026-09-22',
    asset: require('../assets/maptest/corredor_sf_caba_z5.mbtiles'),
  },
};

// Estado del mapa activo (Claude C-5): estado de runtime, no constante.
// D-2 = (a): arranca en santa_fe para no alterar el comportamiento actual.
let mapaActivoId = 'corredor_sf_caba';

export function getMapaActivo(): MapDescriptor {
  const m = CATALOGO[mapaActivoId];
  if (!m) {
    throw new Error(
      'Mapa activo invalido: ' + mapaActivoId +
      '. Mapas disponibles: ' + Object.keys(CATALOGO).join(', ')
    );
  }
  return m;
}

export function setMapaActivo(id: string): void {
  if (!CATALOGO[id]) {
    throw new Error(
      'Mapa no encontrado: ' + id +
      '. Mapas disponibles: ' + Object.keys(CATALOGO).join(', ')
    );
  }
  mapaActivoId = id;
}

export function getMapasDisponibles(): string[] {
  return Object.keys(CATALOGO);
}
