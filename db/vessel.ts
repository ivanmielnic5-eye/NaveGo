// db/vessel.ts
// Ficha singleton de embarcación. Todos los campos son opcionales.
import type { SQLiteDatabase } from 'expo-sqlite';

export type Vessel = {
  nombre: string | null;
  tipo: string | null;
  modelo: string | null;
  eslora: number | null;
  manga: number | null;
  calado: number | null;
  motor: string | null;
  updated_at: number;
};

export async function getVessel(db: SQLiteDatabase): Promise<Vessel | null> {
  const row = await db.getFirstAsync<Vessel>('SELECT * FROM vessel WHERE id = 1');
  return row ?? null;
}

export async function saveVessel(
  db: SQLiteDatabase,
  data: Omit<Vessel, 'updated_at'>
): Promise<void> {
  await db.runAsync(
    `INSERT INTO vessel (id, nombre, tipo, modelo, eslora, manga, calado, motor, updated_at)
     VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       nombre = excluded.nombre,
       tipo = excluded.tipo,
       modelo = excluded.modelo,
       eslora = excluded.eslora,
       manga = excluded.manga,
       calado = excluded.calado,
       motor = excluded.motor,
       updated_at = excluded.updated_at`,
    [
      data.nombre,
      data.tipo,
      data.modelo,
      data.eslora,
      data.manga,
      data.calado,
      data.motor,
      Date.now(),
    ]
  );
}
