# LocationFix
type LocationFix = {
  measuredAt: number;
  receivedAt: number;
  latitude: number;
  longitude: number;
  accuracy: number;
  speed: number | null;
  heading: number | null;
};
