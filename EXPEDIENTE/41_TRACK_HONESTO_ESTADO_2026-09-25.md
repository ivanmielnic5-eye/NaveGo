# TRACK HONESTO — ESTADO AL 2026-09-25

**Fecha:** 2026-09-25
**Estado:** PARCIAL — Estados 1, 2, 4 implementados. Estado 3 pendiente.

---

## Contexto

Cuando se pierde senal GNSS, la app dibujaba una linea recta
entre el ultimo punto antes del corte y el primero despues.
Eso inventa recorrido (violaba D-2026-0003).

Se diseno un "track honesto" con 4 estados. Este documento
registra el estado actual de la implementacion.

---

## Estados y su estado

### Estado 1 — NORMAL (con senal)
- Punto azul se mueve con los fixes.
- Track rojo continuo.
- **Estado:** funcionaba antes, sigue funcionando.

### Estado 2 — GAP ACTIVO (sin senal)
- Punto clavado en el ultimo lugar conocido.
- Titila amarillo (1 Hz).
- Track rojo se corta.
- **Estado:** IMPLEMENTADO Y PROBADO 2026-09-25.
  El Director confirmo visualmente que funciona.

### Estado 3 — RECUPERACION (vuelve la senal)
- Punto salta al nuevo lugar.
- Vuelve a azul.
- Track rojo continua desde B.
- Linea punteada amarilla entre A y B + icono + duracion.
- **Estado:** PARCIAL. El punto salta y vuelve a azul (funciona).
  La linea punteada todavia NO esta implementada (Parte 3 pendiente).

### Estado 4 — HUD con dos numeros
- Distancia registrada + cantidad de gaps + duracion total.
- **Estado:** IMPLEMENTADO Y PROBADO 2026-09-25.
  Formato: "X m registrados · N gap (Ms)".

---

## Lo que se probo en el test del 2026-09-25

Con el escenario 05 (corte de 30 s durante el zigzag):

- El punto azul se clavo al perder senal.
- Titilo amarillo durante 30 s.
- Al recuperar, salto al nuevo punto y volvio a azul.
- El track rojo continuo desde B sin unir A con B.
- El HUD mostro "0 m registrados · 1 gap (31 s)" en amarillo.
- El log confirmo: [GAP] abierto, [GAP] cerrado duracion=31000ms.

**Todo funciono como estaba disenado.**

---

## Bugs arreglados durante la implementacion

1. **Log [GAP] cerrado mostraba duracion=0ms.**
   Causa: el calculo usaba un valor ya sobrescrito.
   Fix: guardar startAt en una ref al abrir el gap.
   Ahora reporta la duracion correcta (31000ms).

2. **Contadores no se reseteaban entre sesiones.**
   Causa: gapCount y gapTotalDurationMs arrancaban con valor
   de la sesion anterior.
   Fix: setGapCount(0) y setGapTotalDurationMs(0) al iniciar.

3. **Sobre-escritura del campo test.** Detectado pero no arreglado.
   El [FIELD-LOG] se dispara dos veces al cerrar sesion
   (263 fixes + 0 fixes). No grave. Pendiente.

---

## Archivos tocados hoy

- useNaveGoTracker.ts: gapCount, gapTotalDurationMs, gapActive,
  gapStartAtMsRef, reset, exponer en return.
- App.tsx: HUD con dos numeros, pasar gapActive al mapa.
- components/MapaOffline.tsx: prop gapActive, Animated titileo,
  color condicional del punto.
- assets/gnss/gnss_simulado.jsonl: escenario 05 (corte 30 s).

## Backups creados

- useNaveGoTracker.ts.pre-hud
- useNaveGoTracker.ts.pre-gapactive
- App.tsx.pre-hud
- App.tsx.pre-gapactive
- components/MapaOffline.tsx.pre-gapactive

---

## Pendiente — Parte 3

- Linea punteada amarilla al recuperar (Estado 3).
- Icono de senal perdida en el punto A.
- Duracion del gap al lado de la linea.

**Decision del diseno:** capa aparte, no parte del track rojo.

---

## Referencias

- EXPEDIENTE/40_CIERRE_BUG_RUIDO_VS_GAP.md
- .logos/dsh-output/diseno_track_honesto_20260925_1630.log

---

*Generado: 2026-09-25*
*Por: DeepSeek (chat) bajo direccion del Director*
