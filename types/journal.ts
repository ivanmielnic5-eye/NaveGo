// types/journal.ts

export interface GPSFix {
  id: string;
  session_id: string;
  sequence_no: number;
  timestamp: number;
  lat_raw: number;
  lon_raw: number;
  alt?: number | null;
  accuracy?: number | null;
  speed?: number | null;
  heading?: number | null;
  quality: 'GOOD' | 'SUSPECT' | 'REJECTED';
  satellites?: number | null;
}