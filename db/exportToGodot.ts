import * as FileSystem from 'expo-file-system';
import { SQLiteDatabase } from 'expo-sqlite';

export async function exportSessionToGodotJson(
  db: SQLiteDatabase,
  sessionId: string,
  targetPath: string = `${FileSystem.documentDirectory}trajectory_data.json`
): Promise<void> {
  try {
    const query = `
      SELECT lat_raw, lon_raw, timestamp, heading 
      FROM gps_fixes 
      WHERE session_id = ? AND quality = 'GOOD' 
      ORDER BY sequence_no ASC;
    `;
    
    const rows = await db.getAllAsync(query, [sessionId]);

    if (!rows || rows.length === 0) {
      console.warn("[EXPORT_GODOT] No se encontraron fixes con calidad 'GOOD' para la sesión:", sessionId);
      return;
    }

    const trajectoryData = rows.map((row: any) => ({
      lat: row.lat_raw,
      lon: row.lon_raw,
      timestamp: row.timestamp,
      heading: row.heading
    }));

    const jsonString = JSON.stringify(trajectoryData, null, 2);
    await FileSystem.writeAsStringAsync(targetPath, jsonString, {
      encoding: FileSystem.EncodingType.UTF8,
    });

    console.log(`[EXPORT_GODOT] Archivo generado exitosamente en: ${targetPath}`);
    console.log(`[EXPORT_GODOT] Total de puntos exportados: ${trajectoryData.length}`);

  } catch (error) {
    console.error("[EXPORT_GODOT] Error al exportar la trayectoria:", error);
  }
}