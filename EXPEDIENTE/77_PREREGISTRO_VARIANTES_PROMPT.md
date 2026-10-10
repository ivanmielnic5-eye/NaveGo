# PREREGISTRO — Comparacion de variantes de prompt

**Fecha:** 2026-10-10
**Autor:** Directora de Investigacion
**Estado:** CONGELADO antes de ejecutar. Cualquier desvio se anota.
**Complementa:** memos 73, 74, 75, 76.

---

## 0. Proposito

Responder: pueden los modelos discriminar acciones dado un estado y una
ESPECIFICACION SUFICIENTE de la mision, sin reglas estado->accion?

Esta es la condicion B de Luna: "el modelo conoce el objetivo pero no logra
elegir". Si falla aqui, es limite real del modelo. Si pasa, era problema de
especificacion (condicion A).

---

## 1. DISENO PREREGISTRADO

### Modelo
- Llama 3.1 8b (via /api/chat + format:json).
- Razon: mejor senal observada con fase prominente (V4 dio 2/3 terminales OK).

### Contextos
- 20 contextos del split DESARROLLO de CC002.
- Balanceados: 5 por accion.
- Seed fija: 777.
- NO se toca el split CONFIRMATORIO.

### Variantes de prompt (3)
- **VA:** prompt actual (contrato pobre, sin reglas estado->accion).
- **VB:** contrato corregido (objetivo operativo + consecuencias de cada accion,
  sin reglas estado->accion).
- **VC:** VB + enfasis visual de campos del estado (formato, no contenido).

### Orden de ejecucion
- VA primero, VB despues, VC despues.
- Mismos 20 contextos para las 3.
- Una corrida por (contexto, variante). Sin repeticiones.

### Metricas a registrar
- Accuracy global por variante.
- Accuracy por accion (4).
- Accuracy por familia (4).
- Matriz de confusion.
- Distribucion de uso de acciones (para detectar colapso).
- JSON valido (%).
- Parametro correcto cuando accion es correcta (%).

### Baselines preregistrados
- Aleatorio uniforme: 25%.
- Prediccion constante (siempre la clase mayoritaria): 25% en CC002.
- Politica explicita simple: se corre DESPUES, como control adicional.

---

## 2. VARIANTES DE PROMPT

### VA — Prompt actual (contrato pobre)
El que esta implementado en armar_prompt. Describe las 4 acciones con
"que hace" pero sin consecuencias operacionales ni objetivo claro.

### VB — Contrato corregido
Estructura:
1. MISION: llegar a la meta de forma segura.
2. ESTADO actual (pos, heading, meta, dist, viento).
3. CONSECUENCIAS de cada accion (que pasa cuando la usas).
4. RESTRICCIONES (terminar solo si dist<15m).
5. PEDIDO de JSON.

Sin reglas "si X usar Y". Sin ejemplos resueltos.

### VC — VB + enfasis visual
Mismos datos que VB pero:
- Campos criticos en MAYUSCULAS.
- Distancia a meta con umbral explicito al lado.
- Separacion visual mas clara entre secciones.

---

## 3. CRITERIO DE EXITO

- **Exito fuerte:** VB o VC superan accuracy 40% con distribucion de uso de
  las 4 acciones (no colapso a 1-2).
- **Exito debil:** VB o VC superan 30% pero siguen sin usar todas las acciones.
- **Fracaso:** VB y VC no superan VA en >5pp.

Si fracaso: documentar como limite del modelo en este dominio y evaluar
opciones C/D/E (few-shot, fine-tuning, cambio de arquitectura).

---

## 4. LO QUE NO SE HACE

- No se corre sobre confirmatorio.
- No se ajusta el prompt despues de ver resultados.
- No se cambia el modelo durante la corrida.
- No se mezclan variantes en la misma corrida.
- No se toca el banco CC002.

---

## 5. FIRMA

**Estado:** CONGELADO antes de ejecutar.
**Proximo paso:** implementar las 3 variantes y correr la comparacion.
**Referencia:** respuesta de Luna 2026-10-10 sobre tension reglas vs discriminacion.
