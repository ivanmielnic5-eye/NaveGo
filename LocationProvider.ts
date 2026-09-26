import * as Location from 'expo-location';

export type LocationCallback = (location: Location.LocationObject) => void;

export interface LocationProvider {
  requestForegroundPermissionsAsync(): Promise<{ status: string }>;
  watchPositionAsync(
    options: Location.LocationOptions,
    callback: LocationCallback,
  ): Promise<{ remove: () => void }>;
}

export const realLocationProvider: LocationProvider = {
  requestForegroundPermissionsAsync: () =>
    Location.requestForegroundPermissionsAsync() as Promise<{ status: string }>,
  watchPositionAsync: (options, callback) =>
    Location.watchPositionAsync(options, callback),
};
