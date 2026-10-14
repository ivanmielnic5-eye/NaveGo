# F-HELD — CONSIGNA SELLADA PARA EL AUTOR

**Version:** 1.0
**Fecha:** 2026-10-13
**Estado:** CONGELADA antes de generar.
**Proposito:** generar 60 formulaciones alternativas de la clausula
de velocidad para F2.

---

## Consigna

Vas a escribir formulaciones en espanol de una clausula de mision
nautica. La clausula expresa una condicion de velocidad maxima.

### Regla abstracta que debe expresar

La mision se considera completa si se cumplen DOS condiciones:

1. La distancia a la meta es MENOR ESTRICTA que un umbral T.
2. La velocidad es MENOR O IGUAL (inclusiva) que un maximo v_max.

Vas a generar SOLO la parte de la clausula de velocidad (la condicion 2).
La clausula se insertara en un prompt mayor, no lo escribas entero.

### Que NO debes usar

NO uses ninguna de estas construcciones (ya existen en el proyecto):

- "menor o igual a X nudos"
- "no supere los X nudos"
- "no este navegando a mas de X nudos"
- "sea como maximo X nudos"

NO escribas ejemplos. NO expliques. NO numeres. Solo la lista de frases.

### Que SI debes producir

60 formulaciones alternativas de la clausula "v <= v_max".

Distribucion obligatoria (respetala):

- 20 en registro formal/tecnico (estilo manual nautico).
- 20 en registro coloquial (estilo conversacion).
- 20 en registro mixto/neutro.

Longitud:

- 20 cortas (menos de 8 palabras).
- 20 medianas (8 a 15 palabras).
- 20 largas (mas de 15 palabras).

Estructura:

- 20 afirmativas ("la velocidad no excede...", "el barco va por debajo de...").
- 20 condicionales ("si la velocidad es...", "en caso de que la velocidad...").
- 20 imperativas/negativas ("no vayas a mas de...", "evita superar...").

### Reglas de calidad

1. Cada formulacion debe ser SEMANTICAMENTE EQUIVALENTE a
   "velocidad <= v_max". Nada de condiciones adicionales.
2. Usa el marcador {vmax} donde va el numero, y "nudos" como unidad.
3. No mezcles la condicion de distancia. Solo velocidad.
4. No uses ambiguedad ("mas o menos", "cerca de").
5. Formulaciones naturales, no rebuscadas.
6. No incluyas numeros concretos. Solo el marcador {vmax}.

### Formato de salida

Una linea por formulacion. Sin numeros, sin bullets, sin comillas.
60 lineas en total.
