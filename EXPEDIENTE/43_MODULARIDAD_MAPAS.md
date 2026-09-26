# NAVEGO COMO SISTEMA MODULAR
# Mapas transitorios, funcionalidades permanentes

**Fecha:** 2026-09-25
**Estado:** PROPUESTA — principio arquitectonico a adoptar
**Expediente relacionado:** 42_INVENTARIO_MAPA

---

## 1. El problema que vimos hoy

Tres sintomas concretos, todos el mismo dia:

1. **Perdimos el auto-follow** al reemplazar `<UserLocation>` nativo
   por `<Marker>` propio. Ganamos control visual, perdimos una
   conducta que vivia dentro del componente nativo.

2. **El boton COURSE-UP quedo huerfano.** El chip dice "COURSE-UP · COG"
   pero nadie lo alimenta. Depende de `smoothedCog`, que ya no existe
   en el tracker. Nadie lo noto durante dias.

3. **El auto-centrado se rompio a la primera vez.** Un `if` con un ref
   que nunca se resetea hizo que la camara siguiera al usuario solo
   en el primer fix. Despues, se alejaba y habia que apretar
   "CENTRAR" a mano. Nadie lo vio durante dias.

Los tres son el mismo problema de fondo.

---

## 2. La causa

`MapaOffline.tsx` hace **todo junto en un solo archivo**:

- Carga el MBTiles.
- Arma el estilo del mapa (20+ capas).
- Declara la camara.
- Dibuja el track.
- Dibuja el punto.
- Maneja los gaps.
- Maneja el centrado.

**Todo depende de todo.** Tocar una capa del estilo puede romper el
centrado. Cambiar el Marker puede romper el auto-follow. Cambiar el
Camera puede romper el track.

Eso explica por que cada iteracion sobre el mapa rompe algo que
ya funcionaba.

---

## 3. La regla

> **Las utilidades de NaveGo no se asocian a ningun mapa.
> Los mapas son transitorios. Las utilidades son permanentes.**

**En una frase:**

> **NaveGo no se adapta al mapa. El mapa se adapta a NaveGo.**

---

## 4. Los tres dominios separados

Separar el mapa en tres capas independientes:

### Capa 1 — Shell (conducta)

- `<Map>` + `<Camera>` + logica de centrado, seguimiento, rotacion.
- Maneja: auto-follow, centrado, Course-Up, deteccion de movimiento
  manual del usuario.
- **Estable.** No se toca al agregar capas visuales ni al cambiar
  de mapa.

### Capa 2 — Style (mapa base)

- Funcion pura que recibe una configuracion y devuelve el estilo
  del mapa.
- Config: que MBTiles, que capas incluir, que colores, que niveles
  de zoom.
- **Swapeable.** Cambiar de mapa sin tocar el shell ni los overlays.

### Capa 3 — Overlays (superposicion)

- Track observado.
- Punto con sus estados (azul / amarillo / gap).
- Linea punteada del gap.
- Peligros, boyas, rutas de referencia, zonas.
- **Independiente por overlay.** Cada uno es un componente propio.

---

## 5. La promesa al usuario

Si mañana cambiamos a un mapa del Parana, del litoral, del sur, o de
cualquier otra region:

- El auto-follow sigue funcionando.
- El auto-centrado sigue funcionando.
- El Course-Up sigue funcionando.
- El track honesto sigue funcionando.
- El HUD sigue funcionando.
- Los gaps siguen registrandose.

**El usuario accede a toda la suite con cualquier mapa.**

**Ningun mapa puede romper una utilidad. Ninguna utilidad puede
romper un mapa.**

---

## 6. Por que es un diferenciador estrategico

Las apps de navegacion comerciales atan funcionalidades al proveedor
de mapa. Cuando cambian de proveedor o de region:

- Pierden capas.
- Pierden funcionalidades.
- El usuario siente que "la app cambio".

NaveGo propone lo opuesto: **el sistema modular garantiza que la
experiencia no cambie cuando cambia el mapa.**

Esto es una fortaleza, no un detalle tecnico. Es parte de la
identidad del proyecto.

---

## 7. Proximos pasos

**Fase 1 — Auto-centrado continuo.** En curso (2026-09-25).

**Fase 2 — Auto-follow.** Detectar cuando el usuario mueve el mapa
a mano y dejar de seguirlo. Reapretando CENTRAR, vuelve.

**Fase 3 — Course-Up.** Rotacion de camara por COG. Chip clickeable
que cicla entre NORTH-UP, HEADING-UP, COURSE-UP.

**Fase 4 — Refactor en 3 capas.** Shell, Style, Overlays.

**Fase 5 — Test de regresion.** Cada utilidad debe sobrevivir a un
cambio de mapa. Se prueba cambiando de MBTiles y verificando que
todo sigue funcionando.

---

## 8. Referencia al inventario

El documento `EXPEDIENTE/42_INVENTARIO_MAPA_2026-09-25.md` es la
lista de utilidades que **no deben perderse nunca** al cambiar de
mapa.

Es la base contra la cual se verifica el principio de modularidad.

---

## 9. Frase oficial

> **NaveGo no se adapta al mapa. El mapa se adapta a NaveGo.
> Las utilidades son permanentes. Los mapas son transitorios.**

---

*Generado: 2026-09-25*
*Por: DeepSeek (chat) bajo direccion del Director*
