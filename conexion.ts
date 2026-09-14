export interface TelemetryData {
  utc: string;
  status: string;
  lat: string;
  lon: string;
  sog: string;
  cog: string;
}

const BRIDGE_URL = 'http://192.168.100.106:8084/log';

export function watchTelemetryStream(onData: (data: TelemetryData) => void): () => void {
  let isRunning = true;

  const fetchData = async () => {
    if (!isRunning) return;
    try {
      const response = await fetch(BRIDGE_URL, { cache: 'no-store' });
      if (!response.ok) return;

      const text = await response.text();
      if (!text.trim()) return;

      let data: any;
      try {
        data = JSON.parse(text);
      } catch {
        return;
      }

      if (data == null || typeof data !== 'object') return;

      const utcRaw = String(data.utc || '');
      const utc =
        utcRaw.length >= 6
          ? `${utcRaw.slice(0, 2)}:${utcRaw.slice(2, 4)}:${utcRaw.slice(4, 6)}`
          : utcRaw || '--:--:--';

      const status = data.valid === 1 ? 'A' : 'V';
      const lat = data.lat && data.lat !== '' ? String(data.lat) : '--';
      const lon = data.lon && data.lon !== '' ? String(data.lon) : '--';
      const sog = data.sog != null && data.sog !== '' ? String(data.sog) : '--';
      const cog = data.cog != null && data.cog !== '' ? String(data.cog) : '--';

      onData({ utc, status, lat, lon, sog, cog });
    } catch (error) {
      // Silenciar errores de red transitorios
    }
  };

  const interval = setInterval(fetchData, 1000);
  fetchData();

  return () => {
    isRunning = false;
    clearInterval(interval);
  };
}
