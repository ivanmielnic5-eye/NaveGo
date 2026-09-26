import * as FileSystem from 'expo-file-system/legacy';
import { Asset } from 'expo-asset';
import * as Location from 'expo-location';
import type { LocationCallback, LocationProvider } from './LocationProvider';

interface RawFix {
  measuredAt: number;
  receivedAt: number;
  latitude: number;
  longitude: number;
  accuracy: number;
  speed: number;
  heading: number;
}

class ReplayLocationProvider implements LocationProvider {
  private fixes: RawFix[] = [];
  private loaded = false;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private stopped = false;

  async requestForegroundPermissionsAsync() {
    return { status: 'granted' };
  }

  private async ensureLoaded() {
    if (this.loaded) return;

    const asset = Asset.fromModule(
      require('./assets/gnss/gnss_simulado.jsonl'),
    );
    await asset.downloadAsync();
    const uri = asset.localUri ?? asset.uri;

    const text = await FileSystem.readAsStringAsync(uri);
    this.fixes = text
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0)
      .map((line) => JSON.parse(line) as RawFix);

    if (this.fixes.length === 0) {
      throw new Error('[REPLAY] gnss_simulado.jsonl vacio o mal formado');
    }

    this.loaded = true;
    console.log(`[REPLAY] ${this.fixes.length} fixes cargados`);
  }

  async watchPositionAsync(
    _options: Location.LocationOptions,
    callback: LocationCallback,
  ): Promise<{ remove: () => void }> {
    await this.ensureLoaded();
    this.stopped = false;

    const t0_real = Date.now();
    const t0_received = this.fixes[0].receivedAt;
    let i = 0;

    const tick = () => {
      if (this.stopped) return;

      const elapsed = Date.now() - t0_real;

      while (
        i < this.fixes.length &&
        this.fixes[i].receivedAt - t0_received <= elapsed
      ) {
        const f = this.fixes[i];
        callback({
          timestamp: t0_real + (f.receivedAt - t0_received),
          coords: {
            latitude: f.latitude,
            longitude: f.longitude,
            altitude: null,
            accuracy: f.accuracy,
            altitudeAccuracy: null,
            heading: f.heading,
            speed: f.speed,
          },
        });
        i++;
      }

      if (i < this.fixes.length) {
        this.timer = setTimeout(tick, 50);
      } else {
        console.log('[REPLAY] escenario agotado');
      }
    };

    this.timer = setTimeout(tick, 0);

    return {
      remove: () => {
        this.stopped = true;
        if (this.timer) clearTimeout(this.timer);
        this.timer = null;
      },
    };
  }
}

export const replayLocationProvider = new ReplayLocationProvider();
