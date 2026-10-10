# SEMANTICA DE ACCIONES Y UTILIDAD DEL ORACULO

**Fecha:** 2026-10-10
**Autor:** Director + consulta a Luna GPT
**Estado:** CONGELADO. Base para ampliar el oraculo.
**Complementa:** memo 73 (decisiones de diseno).

---

## 0. Proposito

Definir la semantica de las 4 acciones, la funcion de utilidad del oraculo, y el tratamiento de empates, viento y seguridad. Este memo cierra el paso 1 del orden de ejecucion del memo 73.

---

## 1. VERIFICACION DEL SIMULADOR (2026-10-10)

Antes de decidir, se verifico:

- NO hay obstaculos, tierra, rocas ni bajios en el simulador.
- El radio de 500m aparece solo en oraculo.py como RADIO_SEGURIDAD_M. Es arbitrario, sin justificacion documentada.
- El viento es CONSTANTE por defecto (viento_variar=False).
- El oraculo NO activa viento variable.
- Los contextos del banco viejo tienen viento aleatorio pero constante por contexto.

---

## 2. SEMANTICA DE LAS 4 ACCIONES

### corregir_rumbo
- Accion: poner el rumbo del barco en el parametro (grados absolutos, 0=norte).
- Tolerancia de ejecucion: 8 grados (provisional, a validar).
- Metrica de parametro: error angular circular.
- Referencia del oraculo: rumbo hacia la meta.

### ir_a_punto
- Accion: navegar hacia (meta_x, meta_z) del contexto.
- Parametro: SIEMPRE igual a la meta del contexto. No waypoints en esta version.
- Tolerancia de ejecucion: 15m.
- Metrica de parametro: error en coordenadas (a definir numericamente).

### frenar
- Accion: reducir velocidad hasta sog_objetivo_kn.
- Objetivo: 0.3 kn (velocidad objetivo, NO tolerancia).
- Semantica: NO detiene completamente. Reduce a velocidad residual.

### terminar
- Accion LOGICA terminal. NO maniobra fisica.
- Valida si dist_meta < 15m -> mision exitosa, estado terminal.
- Invalida si dist_meta >= 15m.
- NO frena automaticamente al terminar. Frenar es otra accion.

---

## 3. SEPARACION DE TOLERANCIAS

Hay dos tipos de tolerancia, NO se confunden:

1. Tolerancia de EJECUCION: cuando la receta termino de hacer su trabajo (8deg, 15m, 0.3kn).
2. Tolerancia de EVALUACION: cuando se acepta el parametro del LLM como correcto.

La tolerancia de evaluacion del parametro es una decision metodologica SEPARADA y se define con el banco.

---

## 4. FUNCION DE UTILIDAD DEL ORACULO

### Rankings actuales (a reemplazar)

Hoy: (safety_violation, -progreso_h_max, -alineacion).

### Propuesta nueva

1. PRIMERO: restricciones de validez y limites operacionales (renombrados como boundary_violation).
2. SEGUNDO: exito de mision (dist < 15m dentro del horizonte).
3. TERCERO: progreso medio temporal en los 4 horizontes.
   - P(t) = d_0 - d(t).
   - Progreso medio = integracion trapezoidal usando 5s, 15s, 30s, 45s.
   - P(0) = 0.
4. CUARTO: alineacion con la meta (criterio secundario, sin mezclar con metros).

### Nota sobre safety_violation

Se renombra a boundary_violation. Mide distancia al origen. NO es una medida de seguridad de navegacion.

---

## 5. HORIZONTES

- Se usan los 4 horizontes: 5s, 15s, 30s, 45s.
- NO se usa solo el maximo.
- Progreso medio temporal por integracion trapezoidal.

---

## 6. EMPATES Y UNICIDAD

- Metrica de unicidad: Delta = U_mejor - U_segunda.
- Umbral numerico: PENDIENTE DE MEDIR. Requiere variabilidad del simulador.
- Casos con Delta < umbral: etiqueta AMBIGUOUS. Se conservan para analisis de regret, NO puntuan en la metrica principal.

---

## 7. VIENTO

- Condicion principal: viento constante (como hoy).
- Condicion de robustez: viento variable (opcional, fase posterior).
- Si es variable: semilla fija por contexto, misma realizacion para todas las acciones de ese contexto.
- El LLM ve SOLO el viento actual. El oraculo puede ver la evolucion futura si tiene la semilla.
- Si el oraculo usa la evolucion futura, es un ORACULO PRIVILEGIADO. Documentar. La comparacion no es perfectamente simetrica.

---

## 8. LO QUE NO SE CIERRA SIN MEDIR

Dos cosas requieren medicion del simulador antes de congelarse:

1. El umbral numerico de unicidad.
2. La validacion fisica de las tolerancias (8deg, 15m).

Asignar valores definitivos ahora seria inventar precision.

---

## 9. ORDEN DE IMPLEMENTACION

1. Congelar esta semantica.
2. Congelar funcion de utilidad y margen de unicidad.
3. Ampliar el oraculo (accion + parametro + puntajes + margen).
4. Tests de regresion: que la ampliacion conserve decisiones de las 3 recetas.
5. Optimizar el costo del oraculo con version de referencia congelada.
6. Generar el banco confirmatorio.

NO optimizar el oraculo mientras se define que significa una decision correcta.

---

## 10. LO QUE NO SE HACE

- No se optimiza el oraculo durante la ampliacion.
- No se generan waypoints intermedios en ir_a_punto.
- No se mezclan metros y grados en un solo escalar sin normalizacion.
- No se elimina la regla de 500m sin antes decidir si el dominio lo requiere.

---

## 11. FIRMA

**Estado:** CONGELADO.
**Proximo paso:** ampliar el oraculo (paso 3 del orden).
**Regla:** sin este memo commiteado, no se toca codigo.
