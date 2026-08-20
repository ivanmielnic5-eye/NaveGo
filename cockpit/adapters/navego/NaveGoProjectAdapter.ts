export function createNaveGoAdapterState(tracker: any) {
  return {
    project: "NaveGo",
    mission: "Registrar una derrota náutica confiable",
    status: tracker.isTracking ? "ACTIVO" : "EN_PAUSA",
    tracking: tracker.isTracking ?? false,
    session: tracker.isTracking ? "Sesión activa" : "Sin sesión activa",
    lastUpdate: tracker.lastFixTimestamp ? new Date(tracker.lastFixTimestamp).toLocaleTimeString() : null,
    health: [
      { name: "GNSS", status: "NO_VERIFICADO" },
      { name: "Tracking", status: tracker.isTracking ? "OK" : "EN_PAUSA" },
    ],
  };
}
