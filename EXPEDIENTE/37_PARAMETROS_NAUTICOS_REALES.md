# PARAMETROS NAUTICOS REALISTAS — REFERENCIA PARA ESCENARIOS

**Fecha:** 2026-09-25
**Motivo:** El ground truth sintetico original usaba viradas cada 30
segundos con angulos de +/-30 grados, instantaneas. Eso no representa
navegacion real de un velero. Este documento fija parametros realistas
para futuros escenarios.

---

## ADVERTENCIA METODOLOGICA

Los valores de este documento son **aproximaciones razonables** basadas
en literatura general de navegacion a vela, no en papers especificos
verificados. Cada valor lleva una marca:

- **[V]** = verificado con fuente especifica
- **[A]** = aproximacion razonable sin fuente directa verificada
- **[INC]** = valor incierto, requiere investigacion adicional

Si un escenario futuro usa un valor de este documento, debe citar la
marca correspondiente. Los valores [A] pueden ajustarse si aparece
mejor informacion.

---

## 1. VIRADAS (maniobras de cambio de rumbo)

### Duracion de la maniobra

| Tipo de barco | Duracion | Marca |
|---|---|---|
| Velero ligero con tripulacion entrenada | 8-15 segundos | [A] |
| Velero de crucero tipico | 20-30 segundos | [A] |
| Velero pesado o poca tripulacion | 1-3 minutos | [A] |

**Uso en escenarios:** usar **20-30 segundos** para una virada suave
(velero de crucero). El barco gira gradualmente, no instantaneamente.

### Cadencia entre viradas

| Contexto | Cadencia | Marca |
|---|---|---|
| Regata con viento fuerte | cada 3-5 minutos | [A] |
| Crucero activo contra el viento | cada 5-10 minutos | [A] |
| Crucero relajado | cada 15-30 minutos | [A] |
| Navegacion oceanica (borde largo) | horas o dias | [A] |

**Uso en escenarios:** para travesias simuladas cortas (5-15 min),
usar **viradas cada 3-5 minutos**. Un tramo de 5 minutos alcanza para
1-2 viradas.

**NUNCA usar viradas cada 30 segundos** — no representa navegacion real.

---

## 2. VELOCIDADES

### Velocidad tipica de un velero

| Condicion | Velocidad | Marca |
|---|---|---|
| Viento muy ligero (brisa) | 1-2 nudos | [A] |
| Viento ligero | 3-4 nudos | [A] |
| Viento moderado (crucero comodo) | 5-6 nudos | [A] |
| Viento fuerte | 7-9 nudos | [A] |
| Regata competitiva | 10-15 nudos | [A] |

**Uso en escenarios:** usar **4-6 nudos** para crucero normal. Es el
rango mas comun en navegacion recreativa.

**Conversion:** 1 nudo = 0.5144 m/s = 1.852 km/h.
5 nudos = 2.57 m/s = 9.26 km/h.

---

## 3. ANGULOS DE VIRADA

### Angulo entre bordes (navegacion contra el viento)

| Situacion | Angulo entre bordes | Marca |
|---|---|---|
| Ceñida cerrada (aprovechando al maximo) | 60-70 grados | [A] |
| Ceñida normal | 80-90 grados | [A] |
| Descuartelado (con viento a favor parcial) | 100-120 grados | [A] |

**Uso en escenarios:** usar **80-90 grados** entre bordes (ceñida normal).
Eso significa viradas de +/-40-45 grados respecto al rumbo medio.

El angulo se logra con una transicion suave de 20-30 segundos, no con
un salto instantaneo.

---

## 4. ACELERACION Y DESACELERACION

### Desde quieto hasta crucero

- Velero a motor arrancando: 10-20 segundos para llegar a crucero [A]
- Velero a vela arrancando: 30-60 segundos (depende del viento) [A]

**Uso en escenarios:** usar **20-30 segundos** para una aceleracion
desde quieto. Gradual, no de golpe.

### Perdida de velocidad en virada

- Un velero bien maniobrado pierde 1-2 nudos en una virada [A]
- Un velero mal maniobrado puede perder 3-4 nudos [A]
- Recuperar la velocidad toma 20-60 segundos [A]

**Uso en escenarios:** para escenarios de stress, **ignorar la perdida
de velocidad en virada** (complejidad innecesaria). Para escenarios de
realismo alto, modelarla.

---

## 5. PARAMETROS NO MODELADOS EN EL SIMULADOR ACTUAL

El simulador actual no modela:

- **Deriva por corriente** — un rio tiene corriente que afecta la
  posicion real independientemente del rumbo del barco. [INC]
- **Viento variable** — el simulador usa viento constante. En la
  realidad el viento rola (cambia de direccion) y oscila en intensidad. [INC]
- **Olas y oleaje** — afecta la posicion instantanea y el rumbo del
  barco. [INC]
- **Corrientes locales** — en un rio hay zonas de corriente diferente
  segun la orilla y la profundidad. [INC]
- **Fondeo y amarre** — el barco puede estar fondeado (quieto, con
  viento pero sin navegacion). El escenario actual arranca siempre
  con movimiento. [INC]

Estos parametros quedan como **pendientes de investigacion** para
escenarios futuros mas realistas.

---

## 6. GUIA PARA NUEVOS ESCENARIOS

### Escenario corto (5 minutos)
- 1 virada a los 2:30 (virada suave, 20-30 segundos)
- Velocidad 4-6 nudos constante
- Zigzag minimo (menos de 100 m de desvio total)

### Escenario medio (15 minutos)
- 3-4 viradas cada 4-5 minutos
- Velocidad 5 nudos promedio
- Derrota claramente curva pero navegable

### Escenario largo (60 minutos)
- 8-12 viradas cada 5-8 minutos
- Velocidad variable (4-7 nudos segun el tramo)
- Tramos largos en el mismo borde entre viradas

---

## 7. LO QUE ESTE DOCUMENTO NO RESUELVE

- No define un tipo especifico de velero (las cifras son genericas).
- No modela el rio especifico (Santa Fe, Parana, etc).
- No define condiciones de viento reales mas alla de lo generico.
- No tiene datos verificados de papers especificos. Todos los numeros
  son aproximaciones [A].

**Para un escenario con anclaje empirico real**, habria que consultar:

- Manuales de vela (RYA, ASA, US Sailing)
- Papers de simulacion de veleros
- Datos de trazado real de veleros (si hubiera disponibles)

Esto queda como pendiente para cuando haya tiempo y recursos.

---

*Generado: 2026-09-25*
*Por: DeepSeek (chat) bajo direccion del Director*
