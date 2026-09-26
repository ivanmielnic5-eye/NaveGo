# INVENTARIO DEL MAPA — 2026-09-25

**Proposito:** antes de refactorizar el mapa, dejar documentado que
tiene que hacer y que hace hoy. Sin esto, cualquier cambio rompe
algo sin que nos demos cuenta.

---

## 1. Que tiene que hacer el mapa de NaveGo

### Obligatorio

- Mostrar el mapa offline (MBTiles v9 con 9 capas).
- Mostrar el track observado (linea roja solida).
- Mostrar la posicion del usuario (punto).
- Mostrar el track de referencia (linea cyan punteada).
- Mostrar peligros y zonas (hazards).
- Auto-seguir al usuario mientras navega.
- Auto-orientar la camara segun el rumbo (Course-Up).

### Estado GNSS sobre el mapa

- Punto azul cuando hay senal.
- Punto amarillo titilando durante gap.
- Track rojo se corta en el gap.
- Linea punteada amarilla entre A y B al recuperar.
- (Pendiente) Icono de senal perdida con duracion al lado.

### Interacciones

- Boton CENTRAR (manual).
- Zoom con gestos.
- (Deseable) Boton para activar/desactivar Course-Up.
- (Deseable) Boton para cambiar de mapa o estilo.

---

## 2. Estado actual — que funciona y que no

### Funciona

- Mapa offline con 20+ capas (administrativas, agua, edificios,
  rutas, nauticas, seamarks, labels).
- Track observado (rojo).
- Track de referencia (cyan punteado).
- Punto azul con doble contorno.
- Punto amarillo titilando durante gap.
- Linea punteada amarilla en el gap (con contorno negro).
- HUD con distancia + gaps.

### No funciona (roto o perdido)

- **Auto-centrado:** la camara sigue al usuario SOLO LA PRIMERA VEZ
  (por bug del `yaCentroRef` que nunca se resetea).
- **Auto-seguimiento continuo:** NO existe. Se perdio al reemplazar
  `<UserLocation>` nativo por `<Marker>`.
- **Auto-orientacion (Course-Up):** el chip del HUD dice "COURSE-UP"
  pero la camara nunca rota. La logica quedo huerfana porque
  `tracker.smoothedCog` ya no existe.
- **Boton cambiar mapa/estilo:** NO existe. El mapa esta hardcodeado.
- **Icono de senal perdida en el gap:** no implementado (Parte 3
  incompleta del track honesto).

### Incertidumbres detectadas

- El `<Camera>` de MapLibre 11.3.10 no expone `followUserLocation`
  en sus tipos. Habria que verificar la API real o usar
  `cameraRef.jumpTo` en cada fix.

---

## 3. Que se perdio respecto a backups

El backup `FUNCIONAL_2026-09-20_09-46` tenia **4 capas** en el estilo
del mapa. El vivo tiene **20+ capas**.

Es decir: el mapa crecio 5x en funcionalidad visual en 5 dias.
Pero perdió la conducta de seguir al usuario, que vivia dentro del
`<UserLocation>` nativo.

### Diferencia clave

| Aspecto | Backup funcional | Vivo |
|---|---|---|
| Componente de ubicacion | `<UserLocation>` nativo | `<Marker>` propio |
| Auto-follow | Si (lo hacia el nativo) | No |
| Control del color | No | Si |
| Control del titileo | No | Si |
| Control del gap | No | Si |
| Capas de estilo | 4 | 20+ |

**Conclusion:** ganamos control visual, perdimos conducta de seguimiento.

---

## 4. Propuesta de refactorizacion

Separar el mapa en 3 capas independientes para que un cambio en una
no rompa las otras:

### Capa 1 — `MapShell` (conducta)
- `<Map>` + `<Camera>` + logica de centrado y seguimiento.
- Maneja: auto-follow, centrado, rotacion por rumbo.
- **Estable.** No se toca al agregar capas visuales.

### Capa 2 — `MapStyleBuilder` (visual del mapa base)
- Funcion pura que recibe config y devuelve el estilo.
- Config: que MBTiles, que capas incluir, que colores.
- **Swapeable.** Cambiar mapa sin tocar shell ni overlays.

### Capa 3 — `MapOverlays` (superposicion)
- Track observado.
- Punto con estados (azul / amarillo / gap).
- Linea punteada del gap.
- Peligros, boyas, rutas de referencia.
- **Independiente por overlay.** Cada uno es un componente.

### Beneficio esperado

- Cambiar de mapa o estilo → NO rompe auto-follow.
- Agregar un overlay → NO rompe el estilo.
- Cambiar el centrado → NO rompe los overlays.

---

## 5. Prioridades de restauracion

**Urgente:**
1. Auto-centrado continuo (bug del `yaCentroRef`).
2. Auto-seguimiento (reemplazar la conducta perdida).

**Importante:**
3. Course-Up funcional (rotacion de camara por COG).
4. Icono de senal perdida en el gap.

**Deseable:**
5. Boton para cambiar de mapa o estilo.
6. Boton para activar/desactivar Course-Up.
7. Refactorizacion en 3 capas.

---

## 6. Que NO toca este inventario

- El estilo visual de las 20+ capas existentes.
- El sistema de glyphs y fuentes.
- La carga del MBTiles.
- El HUD.
- Los sources GeoJSON (trackActivo, trackRef, gapArc).

---

## Referencias

- components/MapaOffline.tsx (562 lineas, vivo)
- backups/FUNCIONAL_2026-09-20_09-46/MapaOffline.tsx (funcional)
- .logos/bin/logos-mem (version del contexto)

---

*Generado: 2026-09-25*
*Por: DeepSeek (chat) bajo direccion del Director*
