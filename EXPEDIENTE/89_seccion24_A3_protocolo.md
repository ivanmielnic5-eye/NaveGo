# SECCION 24 — PROTOCOLO A3 (ADAPTACION DE CONTRATOS)

**Fecha:** 2026-10-13
**Autor:** Direccion de Investigacion
**Estado:** PROPUESTA CONSOLIDADA. No ejecutado.
**Referencias:** memo 89 secciones 19-23, anexos C (Claude), E (Claude),
F (Luna), G (Luna), H (Claude).

---

## 24.1 Contexto

A2 (Fase 1a) ejecutado y validado. Resultado:
- accuracy SFT = 1.000 sobre test_interp (T=11,17,23 no vistos).
- accuracy base = 0.310.
- T_efectivo = 11.135, 17.113, 23.088 (desvio <0.15 m).
- Veredicto: APRENDIO (Fase 1a, interpolacion).

A2 demuestra que el SFT puede aprender una regla determinista simple y
generalizarla a parametros no vistos. NO demuestra que el LLM aporte
valor sobre Python. Esa es la hipotesis de fondo (H1), todavia abierta.

Consulta a Luna (anexo G) y a Claude (anexo H). Ambos convergen en que
el proximo experimento debe aislar una afirmacion concreta:
adaptacion a contratos sin reentrenamiento.

## 24.2 Hipotesis

- **H1a — Capacidad:** el LLM aplica correctamente contratos nuevos sin
  actualizar sus pesos.
- **H1b — Valor comparativo:** el LLM ofrece una ventaja practica frente
  a un motor Python configurable, en al menos una dimension predefinida.
- **H0:** no se observa esa ventaja bajo las condiciones evaluadas.

H1a y H1b no se confunden. Un resultado favorable para H1a no confirma
H1b.

Claridad importante (Claude, anexo H, seccion 6): en familias
deterministas, el motor Python correcto saca 100% por construccion. La
ventaja DECISIONAL del LLM no es testeable ahi. Lo testeable es la
ventaja de INTERFAZ (robustez a formulaciones no vistas) y de ESFUERZO
HUMANO (adaptacion sin desarrollador).

## 24.3 Familias de contratos

Cuatro familias de contrato, en orden de complejidad creciente. El
agente recibe un estado y un contrato (en lenguaje natural). Debe
decidir entre `{ir_a, terminar}` segun el contrato.

**F1 — Umbral.** Terminar si `d < T`. T varia. (Esta es la familia de
A2, sirve de control.)

**F2 — Composicion.** Terminar si `d < T` Y `v <= v_max`. Si no, `ir_a`.
Introduce una condicion adicional.

**F3 — Prioridad de seguridad.** Terminar si `d < T`, EXCEPTO si hay
un obstaculo en la zona de seguridad. Si hay obstaculo, `ir_a`.
Introduce una restriccion con prioridad sobre la condicion principal.

**F4 — Abstencion especificada.** Si falta un dato critico (por ejemplo,
la velocidad no esta disponible), el contrato especifica que la
respuesta correcta es `abstenerse`. Esta familia cambia el espacio de
salida a `{ir_a, terminar, abstenerse}`. Se trata APARTE, en la etapa 3.

Nota: la version de "abstencion como juicio" (no inventar una
resolucion si el contrato es contradictorio) queda FUERA del alcance
de A3. No es seguimiento de contrato, es politica de riesgo. Se difiere
a una fase ulterior.

## 24.4 Factor de formulacion

El motor Python (brazo B) recibe el contrato en especificacion
estructurada. El LLM lo recibe en texto. Esa asimetria es central.

Para medir H1b-interfaz, se necesitan tres conjuntos de formulaciones:

- **F-train:** plantilla de A2. Sin variacion de redaccion.
- **F-dev:** parafrasis, unidades alternativas (mn, m/s), clausulas
  irrelevantes. Se usa para DESARROLLAR el parser de P-text.
- **F-held:** parafrasis nuevas, unidades nuevas, clausulas no vistas.
  Generada por fuente independiente. CONGELADA antes de evaluar.

El LLM y los brazos se evaluan sobre los mismos contextos. La unica
diferencia es como reciben el contrato (texto vs estructura).

## 24.5 Brazos experimentales

Todos los brazos reciben la misma informacion factual del estado.
Difieren en como reciben el contrato y como deciden.

**P-struct — Motor Python con spec estructurada.**
El contrato le llega ya parseado (variable, operador, valor, unidad).
El interprete es fijo; solo cambia la configuracion.
Es el TECHO de capacidad decisional en familias deterministas:
100% por construccion.

**P-text — Motor Python con parser de texto.**
El mismo motor, mas un parser que convierte texto a spec estructurada
(regex, extraccion de numero y unidad, tabla de palabras clave).
Es el costo realista del camino Python sin LLM.
Se desarrolla SOLO contra formulaciones F-dev, con presupuesto de
tiempo acotado y registrado. Se congela antes de evaluar al LLM.

**Hibrido — LLM extrae spec, motor decide.**
El LLM convierte el contrato en JSON estructurado. El motor Python
toma la decision con esa spec.
Si el hibrido iguala al LLM de punta a punta, la recomendacion practica
es el hibrido (decision determinista, mas segura).

**Arbol de decision.**
Entrenado sobre los datos de referencia disponibles (features del
contrato + estado), sin acceso al confirmatorio.
Sirve como baseline de aprendizaje supervisado convencional.

**LLM-A2 (congelado).**
El adaptador de A2, sin reentrenar. Recibe los contratos nuevos en
texto. Es la prueba directa de si el SFT de F1 generaliza a F2, F3, F4.
Se espera que falle en F2+ (solo vio umbrales), pero es evidencia
necesaria.

**LLM-A3.**
SFT sobre F1 + F2, con formulaciones F-train y F-dev (no F-held).
Es el brazo bajo estudio. Se evalua sin reentrenar sobre F-held.

**Brazo techo (opcional, anexo H).**
Un modelo grande zero-shot (por ejemplo, 70B o GPT/Claude). Si resuelve
todas las variantes sin SFT, la propuesta de valor del 8B se desplaza
hacia un modelo pequeno y local, con el grande como techo.

**Probe por cuadrante (etapa 0).**
Con el adaptador de A2 (sin entrenar), evaluar contextos con `d < T` y
`v > v_max`. Etiqueta correcta: `ir_a` (la velocidad incumple).
Si el modelo dice `terminar`, ignora la segunda clausula: solo
memorizo "d < T". Es la prueba mas directa de lectura de contrato vs
regla memorizada, y no cuesta entrenamiento.

## 24.6 Compuertas tecnicas (bloquean si fallan)

Igual que en A2. Si alguna falla, el run es INVALIDO. No refuta nada.

1. Enmascaramiento verificado por inspeccion de tokens.
2. Concordancia puntaje forzado vs generacion en muestra de control.
3. Exactitud en train (puntaje forzado) >= 0.95.
4. Particion por combinaciones, no por filas: ningun contexto de test
   comparte (T, d, v) con uno de train.

## 24.7 Criterios de falsacion preregistrados

Los numeros son propuestas de la Direccion. Se fijan antes de correr.

**H1a — Capacidad de adaptacion:**
- Exactitud de LLM-A3 en F-held >= 0.99 POR FAMILIA, con limite inferior
  de Wilson >= 0.97 (n=300 por familia).
- Se informan resultados por familia. Ninguna queda oculta tras el
  promedio global.

**H1b-interfaz — Ventaja frente a P-text:**
- LLM-A3 supera a P-text por >= 10 puntos en F-held (McNemar pareado,
  p < 0.01), Y
- LLM-A3 no queda mas de 1 punto por debajo de P-struct en la
  formulacion estandar.

**H1b-esfuerzo (exploratorio):**
- Se registra el tiempo y las ediciones de codigo que necesita el motor
  P-text para llegar a >= 99% en formulaciones F-held.
- No es confirmatorio (muestra insuficiente). Se reporta como dato
  descriptivo.

**Seguridad:**
- Definicion de error critico: declarar `terminar` cuando el contrato
  lo prohibe (falso `terminar`).
- Cota superior de error critico preregistrada: <= 1% por familia (con
  n=300, cero errores acota el error a ~1% al 95%).

**Robustez:**
- Parafrasis semanticamente equivalentes no deben producir cambios
  injustificados de accion.
- Tasa de decision consistente >= 0.98.

**Probe por cuadrante (etapa 0):**
- LLM-A2 lee el contrato si acierta >= 0.95 en el cuadrante
  `d < T, v > v_max`.
- Por debajo de 0.5, se declara "ignora la clausula adicional".

## 24.8 Veredicto

El resultado de A3 debe terminar en una de tres conclusiones:

1. **El LLM demuestra adaptacion Y aporta ventaja practica medible**
   frente al baseline competente. -> H1a y H1b respaldadas.

2. **El LLM demuestra adaptacion, pero NO aporta ventaja** frente al
   baseline competente. -> H1a respaldada, H1b no. La utilidad practica
   del LLM queda cuestionada para esta tarea.

3. **El LLM no demuestra adaptacion robusta** bajo las condiciones
   preregistradas. -> H1a no respaldada.

Las tres son resultados utiles. El alcance se limita al artefacto
especifico (modelo, dataset, familias): "el LLM" en general no se
refuta ni se confirma con un solo experimento.

## 24.9 Orden de ejecucion

Cada etapa tiene un corte temprano. Solo se avanza si la anterior pasa.

**Etapa 0 — Cierre de A2 y probe por cuadrante.**
Sin entrenar. Con el adaptador de A2:
1. Analisis por estrato de A2 (tabla por |d-T|).
2. Test emparejado con orden de acciones invertido (invariancia
   semantica).
3. AUC de la base (el 0.310, que es < azar: hay que entender por que).
4. Probe por cuadrante: evaluar F2 con LLM-A2. Cuadrante critico
   `d < T, v > v_max`. Si acierta >= 0.95, lee contrato. Si < 0.5,
   ignora la clausula adicional.
Artefactos: resultados de A2 cerrados + resultado del probe.
Duracion estimada: 1 sesion de Kaggle (~30 min).

**Etapa 1 — Cribado de A3.**
Generar F1+F2, formulaciones F-train/F-dev, splits train/val/F-held.
Entrenar LLM-A3 (1 semilla).
Evaluar: P-struct, P-text, arbol, LLM-A2, LLM-A3.
Aplicar compuertas y cribado 95/90.
Corte: si H1a no se acerca a 0.99 en F-held, parar. NO ir a etapa 2.
Duracion: ~1-2 dias de trabajo + 1 sesion de Kaggle por semilla.

**Etapa 2 — Familia de seguridad (F3).**
Solo si etapa 1 pasa.
Agregar F3 (prioridad de seguridad). Incluir prueba de conflicto
texto-datos (un texto incidental que sugiere la accion contraria).
Agregar brazo hibrido. Correr 3 semillas.
Aplicar criterios de H1a y H1b.
Duracion: ~2-3 dias + 3 sesiones de Kaggle.

**Etapa 3 — Abstencion (F4).**
Se trata aparte, con 3 acciones `{ir_a, terminar, abstenerse}`.
Define cuando abstenerse segun el contrato (no juicio de riesgo).
Familia retenida para confirmatorio independiente.
Duracion: a determinar.

## 24.10 Lo que NO se hace en A3

- NO se prueba "ventaja decisional" en familias deterministas (no es
  testeable: P-struct saca 100% por construccion).
- NO se incluye lazo cerrado ni control fisico (es otra fase).
- NO se incluye conocimiento nautico implicito (requiere verdad con
  fuente documentada, otro experimento).
- NO se modifica A2 ni se reentrena con las familias nuevas para A2
  (A2 queda congelado como artefacto).
- NO se cambian las familias ni los criterios despues de ver
  resultados. Lo que falle, se documenta.

## 24.11 Decisiones pendientes del Director

1. **¿Se aprueba el protocolo A3 integrado (Luna + Claude)?**
2. **¿Cual es el SFT para el brazo LLM-A3?** ¿Reentrenar desde el
   adaptador de A2, o desde Llama base?
3. **¿Se aprueba el preregistro numerico** (0.99 por familia, 10 puntos
   frente a P-text, error critico <= 1%)?
4. **¿Se ejecuta etapa 0 primero** (es barata y de bajo riesgo)?
5. **¿Se incluye el brazo techo zero-shot** (modelo grande) en la
   etapa 1?

## 24.12 Firma

**Estado:** PROPUESTA CONSOLIDADA. Espera aprobacion del Director.
**Proximo paso:** decision del Director sobre las 5 preguntas.
**Regla:** calidad primero, performance despues.
