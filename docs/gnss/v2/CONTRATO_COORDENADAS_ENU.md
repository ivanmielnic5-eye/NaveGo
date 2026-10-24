# Contrato de coordenadas ENU — GNSS V2

## 1. Marco de referencia

El Ground Truth (GT) usa un marco local ENU (East, North, Up).
Las posiciones están expresadas en metros respecto del origen local.

- `pos_x`: Este, positivo hacia el Este.
- `pos_y`: Norte, positivo hacia el Norte.
- `pos_z`: vertical, positivo hacia arriba.

Este contrato pertenece al experimento GNSS. No se deben asumir las
convenciones de ejes de Blender, Godot u otros motores gráficos.
Las integraciones externas deben convertir sus coordenadas explícitamente.

## 2. Convención de rumbo

Los ángulos se expresan en grados, medidos desde el Norte y en sentido
horario:

- 0°: Norte.
- 90°: Este.
- 180°: Sur.
- 270°: Oeste.

Para velocidad horizontal `v` en m/s y un intervalo `dt` en segundos:

    dx = v * dt * sin(theta)
    dy = v * dt * cos(theta)

Por tanto, `dx` corresponde al eje Este y `dy` al eje Norte.

Un cambio de rumbo positivo representa un giro en sentido horario.

## 3. COG y HDG

COG representa el rumbo de avance sobre el fondo; HDG representa el rumbo
de proa. Son magnitudes distintas y no deben considerarse equivalentes
en general.

La trayectoria sintética de virada actual fija ambos valores iguales como
simplificación del modelo. Esta decisión no constituye una equivalencia
náutica general.

## 4. Conversión geográfica del simulador

El simulador GNSS recibe las coordenadas horizontales del GT:

- `pos_x` se convierte en desplazamiento de longitud.
- `pos_y` se convierte en desplazamiento de latitud.
- `pos_z` no se usa para el desplazamiento horizontal.

La conversión aproximada empleada depende de la latitud de referencia:

    dlat = dy / 110540
    dlon = dx / (111320 * cos(lat0))

Los desplazamientos están expresados en metros y los resultados en grados.

## 5. Pruebas y límites de validación

Las pruebas permanentes se encuentran en:

    docs/gnss/v2/tests/test_coordinates.py

Cubren los cardinales geográficos, los cardinales del GT, la geometría de
la virada, la compatibilidad geométrica de Fase A y la conexión de ejes
entre el GT y el simulador.

La aprobación de estas pruebas no equivale todavía a una validación
integral de extremo a extremo GT–GNSS para una virada. Esa integración
debe verificarse por separado.

Los resultados históricos no se regeneran ni se sobrescriben como parte
de esta corrección.

## 6. Estado de validación — 2026-10-20

### Controles aprobados

- Pruebas permanentes de coordenadas: 5/5.
- Compatibilidad geométrica de Fase A: 900 puntos, sin discrepancias.
- Integración sintética GT-GNSS: 300 puntos.
- La integración comprobó latitud, longitud y rumbo con ruido, cortes
  y saltos artificiales desactivados.
- Los archivos históricos no se regeneraron ni sobrescribieron.

### Alcance pendiente

La integración validada cubre una virada sintética y la conversión
geográfica local. No valida todavía el filtro GNSS con ruido o cortes,
ni habilita la Fase B del evaluador.

Los cambios de código permanecen pendientes de revisión final y commit.
