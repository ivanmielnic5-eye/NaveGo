// Funciones puras de geometría/cinemática náutica. Sin estado, sin
// efectos secundarios — fáciles de testear de forma aislada.

const EARTH_RADIUS_M = 6371000; // radio medio terrestre, en metros

function toRadians(degrees: number): number {
  return (degrees * Math.PI) / 180;
}

/**
 * Distancia entre dos coordenadas geográficas (fórmula de Haversine).
 * Adecuada para las distancias cortas/medias de navegación fluvial:
 * el error de asumir la Tierra como esfera perfecta es despreciable
 * en este rango, muy por debajo del ruido propio del GPS.
 *
 * @returns distancia en metros.
 */
export function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  const rLat1 = toRadians(lat1);
  const rLat2 = toRadians(lat2);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(rLat1) * Math.cos(rLat2) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  return EARTH_RADIUS_M * c;
}

/**
 * Rumbo inicial (bearing) entre dos coordenadas, en grados [0, 360).
 * Útil para derivar bearing_deg de un segmento cuando no hay heading
 * directo del GPS disponible.
 */
export function calculateBearing(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const rLat1 = toRadians(lat1);
  const rLat2 = toRadians(lat2);
  const dLon = toRadians(lon2 - lon1);

  const y = Math.sin(dLon) * Math.cos(rLat2);
  const x =
    Math.cos(rLat1) * Math.sin(rLat2) -
    Math.sin(rLat1) * Math.cos(rLat2) * Math.cos(dLon);

  const bearingRad = Math.atan2(y, x);
  return ((bearingRad * 180) / Math.PI + 360) % 360;
}

const KNOTS_PER_MPS = 1.943844; // 1 m/s = 1.943844 nudos náuticos
const METERS_PER_NAUTICAL_MILE = 1852;

/** Convierte velocidad de metros/segundo a nudos náuticos. */
export function mpsToKnots(metersPerSecond: number): number {
  return metersPerSecond * KNOTS_PER_MPS;
}

/** Convierte distancia de metros a millas náuticas. */
export function metersToNauticalMiles(meters: number): number {
  return meters / METERS_PER_NAUTICAL_MILE;
}


