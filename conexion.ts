export interface TelemetryData {
  utc: string;
  status: string;
  lat: string;
  lon: string;
  sog: string;
  cog: string;
}

export function watchTelemetryStream(onData: (data: TelemetryData) => void): () => void {
  let isRunning = true;

  const fetchData = async () => {
    if (!isRunning) return;
    try {
      const response = await fetch('http://localhost:8084/log', { cache: 'no-store' });
      if (!response.ok) return;
      const text = await response.text();
      if (!text.includes('$GPRMC')) return;

      const parts = text.split('|');
      const gprmcLine = parts.length > 1 ? parts[1].trim() : text.trim();
      const tokens = gprmcLine.split(',');

      if (tokens.length >= 9 && tokens[0] === '$GPRMC') {
        const utcRaw = tokens[1] || '';
        const utc = utcRaw.length >= 6  
          ? `${utcRaw.slice(0, 2)}:${utcRaw.slice(2, 4)}:${utcRaw.slice(4, 6)}`  
          : utcRaw;
          
        const status = tokens[2] || '';
        const latVal = tokens[3] || '';
        const latNS = tokens[4] || '';
        const lonVal = tokens[5] || '';
        const lonEW = tokens[6] || '';
        const sog = tokens[7] || '';
        const cog = tokens[8] || '';

        onData({
          utc,
          status,
          lat: latVal ? `${latVal} ${latNS}` : '--',
          lon: lonVal ? `${lonVal} ${lonEW}` : '--',
          sog: sog || '--',
          cog: cog || '--',
        });
      }
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
