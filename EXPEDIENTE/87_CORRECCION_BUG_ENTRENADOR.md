# CORRECCION DE DIAGNOSTICO — Bug del Entrenador v1

**Fecha:** 2026-10-11
**Autor:** Directora de Investigacion
**Estado:** CORRECCION. Reconoce un error de analisis.
**Complementa:** memos 83, 84, 85, 86.

---

## 0. Proposito

Documentar la correccion del diagnostico del memo 86. El "hallazgo grave"
del 67% de error del Entrenador era un artefacto de un bug, no un
hallazgo real.

---

## 1. QUÉ DIJIMOS EN EL MEMO 86

- El Entrenador "miope" produce etiquetas incorrectas.
- 67% de error en corregir_rumbo.
- 100% de error en frenar.
- Convergencia a 240s.

Verificado con 3 chequeos:
- Chequeo 1: margenes reales (94% > 5m).
- Chequeo 2: 240s estable.
- Chequeo 3: viento no afecta.

---

## 2. QUÉ ENCONTRAMOS AHORA

Luna (en su respuesta al memo 86) sospecho:

> "Si corregir_rumbo es una maniobra preparatoria que gira el barco sin
>  avanzar e ir_a_punto gira mientras navega, ejecutar cada accion durante
>  240s sin una continuacion comun podria ser una comparacion injusta."

Al revisar el codigo del Entrenador, se CONFIRMA su sospecha.

### El bug

En _simular_receta:
    corregir_rumbo(b, objetivo_deg=rumbo, timeout_s=timeout_s)

Cada receta corre HASTA QUE TERMINA o hasta el timeout, lo que pase primero.

- corregir_rumbo termina cuando el barco esta alineado (~10-20s).
- ir_a_punto termina cuando llega a la meta (o timeout).
- frenar termina cuando el barco esta lento (~30s).

Cada receta tiene una duracion efectiva DISTINTA.

Pero en _evaluar_una se mide DISTANCIA FINAL en el horizonte. Para cada
receta, la distancia final se mide cuando la receta termino, no cuando
se cumple el horizonte.

Ejemplo:
- corregir_rumbo a horizonte 45s: se alinea a los 10s, queda parado 35s.
  Distancia recorrida: ~20m.
- ir_a_punto a horizonte 45s: navega los 45s completos.
  Distancia recorrida: ~80m.

El Entrenador dice "ir_a_punto progreso mas, es mejor".

Pero no es mejor. Corrio 4 veces mas tiempo.

---

## 3. CONSECUENCIAS

### Sobre el memo 86
El hallazgo de "67% de error del Entrenador" es un ARTEFACTO del bug,
no un error del Entrenador. El memo 86 queda PARCIALMENTE OBSOLETO.

Lo que sigue siendo valido del memo 86:
- Los datos crudos (los tests corrieron, midieron algo).
- La observacion de que la decision cambia con el horizonte.
- La observacion de que frenar no aparece como optima.

Lo que queda INVALIDADO:
- "El Entrenador se equivoca en 67% de los casos".
- "El LLM era mejor que el Entrenador".
- "El hallazgo cambia el diagnostico del proyecto".
- La interpretacion fisica del radio de giro (era el bug, no la fisica).

### Sobre el SFT (memo 83)
El SFT sigue valido. Fue entrenado contra las etiquetas del Entrenador v1.
Su 65% de accuracy es valido como concordancia con esas etiquetas.

### Sobre el proyecto
- No hay que re-etiquetar todavia.
- No hay que reformar el horizonte todavia.
- Primero hay que ARREGLAR EL BUG del Entrenador.

---

## 4. LA CORRECCION

El Entrenador v2 necesita "continuacion comun":

1. Correr cada receta hasta que termine (o timeout).
2. Si termina ANTES del horizonte, aplicar una politica de continuacion
   neutra hasta llegar al horizonte.
3. Medir progreso al horizonte, no al momento en que la receta termino.

La politica de continuacion:
- Debe ser determinista.
- Debe ser neutra (no favorecer ninguna receta).
- Candidato: piloto Python (timon_python), que ya existe.

Ejemplo con continuacion:
- corregir_rumbo: se alinea a los 10s. A los 10s, arranca piloto Python.
  De 10s a 45s, el barco navega con piloto Python.
- ir_a_punto: navega los 45s completos.
- AHORA SI, comparables.

---

## 5. LECCION METODOLOGICA

Este error es simetrico al que detectamos en el Entrenador:
- El Entrenador medía mal porque comparaba recetas de duraciones distintas.
- Nosotros analizamos mal porque no verificamos la semantica de las recetas.

Luna nos aviso. No lo escuchamos lo suficiente en el memo 86.

REGLA NUEVA: antes de auditar cualquier sistema, verificar que las
comparaciones internas sean justas.

---

## 6. PROXIMOS PASOS

1. Marcar el memo 86 como parcialmente obsoleto (agregar aviso).
2. Congelar el Entrenador v1 (con su bug) como evidencia historica.
3. Disenar Entrenador v2 con continuacion comun.
4. Re-correr los tests de convergencia y sensibilidad con v2.
5. Recien ahi, si aparecen hallazgos, reformar y re-etiquetar.
6. Avisar a Luna que su diagnostico fue correcto.

---

## 7. LO QUE NO SE HACE

- NO se re-etiqueta el banco CC002 todavia.
- NO se reforma el horizonte todavia.
- NO se re-entrena el SFT todavia.
- NO se toca el banco confirmatorio.

---

## 8. FIRMA

**Estado:** CORRECCION RECONOCIDA.
**Proximo paso:** memo 88 (diseno del Entrenador v2).
**Referencia:** respuesta de Luna al memo 86.
