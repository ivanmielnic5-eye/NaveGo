# HUD SPEC — NaveGo Simulador / Escuela

Fecha: 2026-08-25

## 1. Propósito

El HUD del simulador debe servir a dos públicos:

- Modo Instrumento: laboratorio técnico para auditoría y validación.
- Modo Escuela: experiencia lúdica para aprender navegación.

Ambos comparten un núcleo común de telemetría, pero cambian la presentación y el feedback.

## 2. Núcleo común (siempre presente)

- Brújula (COG, HDG, SOG)
- Panel de viento (AWS, AWA, TWS, TWA)
- Posición (LAT/LON simulada)
- Estado de sensores
- Controles de cámaras

## 3. Modo Instrumento (Investigación)

- Valores exactos sin redondeo.
- Estado diferencial (error de estima).
- Zona activa del Landscape.
- Sin decoraciones lúdicas.
- Ideal para validar Ground Truth.

## 4. Modo Escuela (Lúdico)

- Misiones simples:
  - Salir del puerto sin tocar bordes.
  - Mantener rumbo 090° durante 20 segundos.
  - Pasar entre boyas.
  - Amarrar en zona verde.

- Feedback:
  - Estrellas por precisión.
  - Mensajes de ánimo.
  - Ayudas visuales (flechas de viento, línea de rumbo sugerida, zona destino).
  - Sonidos suaves de éxito o alerta amable.

- Curva de aprendizaje:
  1. Timón.
  2. Viento y velas.
  3. Corrientes y deriva.
  4. Navegación sin GPS.

## 5. Regla de oro

La verdad física nunca se degrada.
La capa lúdica es solo presentación, nunca modifica la simulación.

## 6. Conexión con la embarcación y territorio

- El HUD lee datos de:
  - LandscapeV2 (Ground Truth)
  - HeadingWindIntegrator (HDG, COG, SOG, viento)
  - SailboatBody (posición, velocidad)

- El HUD no escribe sobre el barco.
- El territorio (zonas funcionales) informa al HUD sobre condiciones de prueba.

## 7. Próximos pasos

- Definir wireframe final del HUD.
- Implementar núcleo común en Godot.
- Crear modo Escuela como capa visual encima del núcleo.
