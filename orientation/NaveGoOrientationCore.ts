import {
  Accelerometer,
  Gyroscope,
  Magnetometer,
} from 'expo-sensors';

export type OrientationConfidence =
  | 'HIGH'
  | 'MEDIUM'
  | 'LOW'
  | 'UNAVAILABLE';

export interface OrientationState {
  magneticHeading: number | null;
  smoothedHeading: number | null;

  headingAccuracy: number | null;

  confidence: OrientationConfidence;

  calibrated: boolean;

  magneticFieldStrength: number | null;

  timestamp: number;

  sensorAvailable: boolean;
}

export interface OrientationCoreOptions {
  updateIntervalMs?: number;

  /*
   * Peso del magnetómetro en la corrección
   * del filtro complementario.
   *
   * 0.02 = muy estable
   * 0.05 = recomendado inicialmente
   * 0.10 = más reactivo
   */
  magnetometerCorrection?: number;

  /*
   * Umbral aproximado para considerar que
   * el campo magnético está siendo perturbado.
   *
   * El campo terrestre normalmente está en
   * un orden de decenas de μT, pero el valor
   * real depende de la ubicación.
   */
  magneticFieldMinUT?: number;

  magneticFieldMaxUT?: number;
}

const DEFAULT_OPTIONS: Required<OrientationCoreOptions> = {
  updateIntervalMs: 50,
  magnetometerCorrection: 0.05,
  magneticFieldMinUT: 20,
  magneticFieldMaxUT: 100,
};

function normalize360(degrees: number): number {
  return ((degrees % 360) + 360) % 360;
}

function normalize180(degrees: number): number {
  let value = ((degrees + 180) % 360) - 180;

  if (value <= -180) {
    value += 360;
  }

  return value;
}

function shortestAngleDifference(
  from: number,
  to: number
): number {
  return normalize180(to - from);
}

function circularLerp(
  current: number,
  target: number,
  alpha: number
): number {
  const difference = shortestAngleDifference(current, target);

  return normalize360(
    current + difference * alpha
  );
}

function magnitude3(
  x: number,
  y: number,
  z: number
): number {
  return Math.sqrt(
    x * x +
    y * y +
    z * z
  );
}

/**
 * NaveGo Orientation Core
 *
 * Responsabilidad:
 *
 *   sensores
 *      ↓
 *   heading magnético
 *      ↓
 *   validación
 *      ↓
 *   filtro complementario
 *      ↓
 *   estado de orientación
 *
 * NO conoce:
 * - MapView
 * - SQLite
 * - HUD
 * - GPS
 * - COG
 * - SOG
 *
 * El resultado magnético queda separado de cualquier
 * corrección náutica posterior (dm + δ).
 */
export class NaveGoOrientationCore {
  private options: Required<OrientationCoreOptions>;

  private magnetometerSubscription: any = null;
  private accelerometerSubscription: any = null;
  private gyroscopeSubscription: any = null;

  private running = false;

  private magnetometerAvailable = false;
  private accelerometerAvailable = false;
  private gyroscopeAvailable = false;

  private latestMagneticHeading: number | null = null;
  private latestSmoothedHeading: number | null = null;

  private latestFieldStrength: number | null = null;

  private latestGyroZ = 0;

  private lastGyroTimestamp: number | null = null;
  private lastUpdateTimestamp = 0;

  private calibrated = false;

  private confidence: OrientationConfidence =
    'UNAVAILABLE';

  private headingAccuracy: number | null = null;

  private listeners = new Set<
    (state: OrientationState) => void
  >();

  constructor(
    options: OrientationCoreOptions = {}
  ) {
    this.options = {
      ...DEFAULT_OPTIONS,
      ...options,
    };
  }

  /**
   * Inicia los sensores.
   */
  async start(): Promise<void> {
    if (this.running) {
      return;
    }

    const [
      magnetometerAvailable,
      accelerometerAvailable,
      gyroscopeAvailable,
    ] = await Promise.all([
      Magnetometer.isAvailableAsync(),
      Accelerometer.isAvailableAsync(),
      Gyroscope.isAvailableAsync(),
    ]);

    this.magnetometerAvailable =
      magnetometerAvailable;

    this.accelerometerAvailable =
      accelerometerAvailable;

    this.gyroscopeAvailable =
      gyroscopeAvailable;

    if (!magnetometerAvailable) {
      this.confidence = 'UNAVAILABLE';

      this.emit();

      return;
    }

    Magnetometer.setUpdateInterval(
      this.options.updateIntervalMs
    );

    if (accelerometerAvailable) {
      Accelerometer.setUpdateInterval(
        this.options.updateIntervalMs
      );
    }

    if (gyroscopeAvailable) {
      Gyroscope.setUpdateInterval(
        this.options.updateIntervalMs
      );
    }

    this.running = true;

    this.subscribeSensors();
  }

  /**
   * Detiene los sensores.
   */
  stop(): void {
    this.magnetometerSubscription?.remove();
    this.accelerometerSubscription?.remove();
    this.gyroscopeSubscription?.remove();

    this.magnetometerSubscription = null;
    this.accelerometerSubscription = null;
    this.gyroscopeSubscription = null;

    this.running = false;

    this.lastGyroTimestamp = null;
    this.latestGyroZ = 0;
  }

  /**
   * Permite a la UI observar el estado sin acoplarse
   * directamente a los sensores.
   */
  subscribe(
    listener: (state: OrientationState) => void
  ): () => void {
    this.listeners.add(listener);

    listener(this.getState());

    return () => {
      this.listeners.delete(listener);
    };
  }

  /**
   * Estado actual.
   */
  getState(): OrientationState {
    return {
      magneticHeading:
        this.latestMagneticHeading,

      smoothedHeading:
        this.latestSmoothedHeading,

      headingAccuracy:
        this.headingAccuracy,

      confidence:
        this.confidence,

      calibrated:
        this.calibrated,

      magneticFieldStrength:
        this.latestFieldStrength,

      timestamp:
        this.lastUpdateTimestamp,

      sensorAvailable:
        this.magnetometerAvailable,
    };
  }

  /**
   * Reinicia el filtro sin detener los sensores.
   *
   * Útil para una futura acción:
   * "RECALIBRAR ORIENTACIÓN".
   */
  reset(): void {
    this.latestMagneticHeading = null;
    this.latestSmoothedHeading = null;

    this.latestFieldStrength = null;

    this.lastGyroTimestamp = null;

    this.headingAccuracy = null;

    this.calibrated = false;

    this.confidence = 'UNAVAILABLE';

    this.lastUpdateTimestamp = 0;

    this.emit();
  }

  private subscribeSensors(): void {
    this.magnetometerSubscription =
      Magnetometer.addListener(
        ({ x, y, z }) => {
          this.processMagnetometer(
            x,
            y,
            z
          );
        }
      );

    if (this.accelerometerAvailable) {
      this.accelerometerSubscription =
        Accelerometer.addListener(
          () => {
            /*
             * Reservado para la siguiente etapa:
             * tilt compensation.
             *
             * No se utiliza todavía para afirmar
             * una orientación absoluta.
             */
          }
        );
    }

    if (this.gyroscopeAvailable) {
      this.gyroscopeSubscription =
        Gyroscope.addListener(
          ({ z, timestamp }) => {
            this.processGyroscope(
              z,
              timestamp
            );
          }
        );
    }
  }

  private processMagnetometer(
    x: number,
    y: number,
    z: number
  ): void {
    if (
      !Number.isFinite(x) ||
      !Number.isFinite(y) ||
      !Number.isFinite(z)
    ) {
      this.confidence = 'UNAVAILABLE';

      this.emit();

      return;
    }

    const fieldStrength =
      magnitude3(x, y, z);

    this.latestFieldStrength =
      fieldStrength;

    /*
     * Primera detección de perturbación magnética.
     *
     * Esto NO pretende reemplazar una calibración
     * hard-iron / soft-iron. Es solamente un guard
     * para evitar presentar como confiable una medida
     * físicamente sospechosa.
     */
    const fieldInExpectedRange =
      fieldStrength >=
        this.options.magneticFieldMinUT &&
      fieldStrength <=
        this.options.magneticFieldMaxUT;

    /*
     * Primera versión:
     *
     * Para un teléfono mantenido aproximadamente
     * horizontal, X/Y permiten obtener el azimut
     * magnético.
     *
     * La compensación completa de inclinación queda
     * explícitamente para la siguiente iteración,
     * donde utilizaremos el vector gravitacional.
     */
    const rawHeading =
      normalize360(
        Math.atan2(y, x) *
          (180 / Math.PI) +
          90
      );

    if (!Number.isFinite(rawHeading)) {
      this.confidence = 'UNAVAILABLE';

      this.emit();

      return;
    }

    this.latestMagneticHeading =
      rawHeading;

    /*
     * Si el campo está fuera del rango esperado,
     * mantenemos el dato pero reducimos confianza.
     */
    if (!fieldInExpectedRange) {
      this.confidence = 'LOW';
      this.headingAccuracy = null;
    } else {
      this.updateFilteredHeading(
        rawHeading
      );

      this.updateConfidence(
        fieldStrength
      );
    }

    this.lastUpdateTimestamp =
      Date.now();

    this.emit();
  }

  private processGyroscope(
    z: number,
    timestampSeconds: number
  ): void {
    if (
      !Number.isFinite(z) ||
      !Number.isFinite(timestampSeconds)
    ) {
      return;
    }

    this.latestGyroZ = z;

    if (
      this.latestSmoothedHeading === null
    ) {
      this.lastGyroTimestamp =
        timestampSeconds;

      return;
    }

    if (
      this.lastGyroTimestamp === null
    ) {
      this.lastGyroTimestamp =
        timestampSeconds;

      return;
    }

    const dt =
      timestampSeconds -
      this.lastGyroTimestamp;

    this.lastGyroTimestamp =
      timestampSeconds;

    /*
     * Protección contra saltos producidos por
     * suspensión/background o timestamps anómalos.
     */
    if (
      dt <= 0 ||
      dt > 0.5
    ) {
      return;
    }

    /*
     * El giroscopio entrega rad/s.
     */
    const gyroDegrees =
      z *
      dt *
      (180 / Math.PI);

    this.latestSmoothedHeading =
      normalize360(
        this.latestSmoothedHeading +
          gyroDegrees
      );
  }

  private updateFilteredHeading(
    magneticHeading: number
  ): void {
    /*
     * Si todavía no existe una referencia,
     * inicializamos directamente desde el magnetómetro.
     */
    if (
      this.latestSmoothedHeading === null
    ) {
      this.latestSmoothedHeading =
        magneticHeading;

      this.calibrated = true;

      this.headingAccuracy = 15;

      return;
    }

    /*
     * Filtro complementario:
     *
     * - gyro = respuesta rápida
     * - magnetómetro = referencia absoluta
     *
     * La integración del gyro ocurre en
     * processGyroscope().
     *
     * El magnetómetro corrige lentamente el drift.
     */
    this.latestSmoothedHeading =
      circularLerp(
        this.latestSmoothedHeading,
        magneticHeading,
        this.options
          .magnetometerCorrection
      );

    this.calibrated = true;

    /*
     * Primera estimación conservadora.
     *
     * No es todavía una precisión instrumental
     * certificada.
     */
    const error =
      Math.abs(
        shortestAngleDifference(
          this.latestSmoothedHeading,
          magneticHeading
        )
      );

    this.headingAccuracy =
      Math.max(
        3,
        Math.min(
          30,
          error * 1.5
        )
      );
  }

  private updateConfidence(
    fieldStrength: number
  ): void {
    if (
      !this.calibrated ||
      this.latestSmoothedHeading === null
    ) {
      this.confidence =
        'UNAVAILABLE';

      return;
    }

    const error =
      this.headingAccuracy ?? 30;

    if (
      fieldStrength <
        this.options.magneticFieldMinUT ||
      fieldStrength >
        this.options.magneticFieldMaxUT
    ) {
      this.confidence = 'LOW';

      return;
    }

    if (error <= 8) {
      this.confidence = 'HIGH';
    } else if (error <= 18) {
      this.confidence = 'MEDIUM';
    } else {
      this.confidence = 'LOW';
    }
  }

  private emit(): void {
    const state =
      this.getState();

    this.listeners.forEach(
      (listener) => {
        try {
          listener(state);
        } catch (error) {
          console.warn(
            '[NOC] Listener error:',
            error
          );
        }
      }
    );
  }
}

/**
 * Factory conveniente.
 *
 * No crea sensores hasta que start() sea llamado.
 */
export function createNaveGoOrientationCore(
  options?: OrientationCoreOptions
): NaveGoOrientationCore {
  return new NaveGoOrientationCore(
    options
  );
}