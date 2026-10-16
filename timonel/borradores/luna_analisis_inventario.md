# BORRADOR — LUNA: ANALISIS DEL INVENTARIO DE TIMONEL

**Fecha:** 2026-10-13
**Estado:** BORRADOR. Fuera del expediente hasta validacion cruzada con Claude.
**Origen:** analisis del inventario seccion 26.

---

# Analisis tecnico del inventario de Timonel — Base para A3

## Dictamen

El inventario permite diseñar el contrato inicial, pero todavia no permite definir una politica de navegacion completa ni afirmar que Timonel respeta restricciones de seguridad.

Hay tres problemas prioritarios:

1. Desalineacion del contrato: el banco A2/A3 permite un umbral T variable, mientras que el simulador declara completada la mision a una distancia fija inferior a 15 m.
2. Acciones sin semantica suficientemente diferenciada: rumbo e ir_a pueden apuntar al mismo lugar, y frenar carece de una condicion formal que determine cuando corresponde.
3. Seguridad no representada en el entorno: sin colisiones, obstaculos ni limites del mundo, no se puede medir de forma valida la prevencion de esos peligros.

Mi recomendacion es no empezar F3 todavia. Primero hay que establecer un contrato comun entre el banco, el interprete y el simulador. Despues se puede incorporar una variable nueva por fase.

En lo que sigue distingo los hechos del inventario de las propuestas de arquitectura. No estoy confirmando el codigo de manera independiente: tomo el inventario suministrado como evidencia de trabajo.

## 1. Analisis del inventario

| Hallazgo | Evaluacion |
| --- | --- |
| rumbo(theta, horizonte_s) | Correcto como primitiva de control de alto nivel si theta representa un rumbo absoluto. Falta especificar el sistema angular, el sentido de giro y el tratamiento del cruce 0/360. |
| ir_a(meta_x, meta_z, horizonte_s) | Adecuado para navegacion a un punto. Debe definirse el sistema de coordenadas, el marco de referencia y el criterio de llegada. |
| frenar(horizonte_s, sog_objetivo_kn=0.3) | El parametro sugiere control de velocidad objetivo, no una orden de frenado fisico instantaneo. El nombre podria inducir a error. |
| terminar(meta_x, meta_z, horizonte_s) | Mezcla la declaracion de finalizacion con argumentos de navegacion. Hay que comprobar si mueve el barco, evalua la llegada o ambas cosas. |
| PID con Ki=0 | Segun el inventario, es un controlador PD en la practica. No demuestra por si solo estabilidad o seguridad en todos los estados. |
| Continuacion comun hasta el horizonte maximo | Util para comparar acciones bajo una ventana temporal comun. Pero hay que confirmar que ocurre despues de alcanzar la meta o violar una condicion. |
| Peligro inminente y boundary de 500 m | Son criterios del entrenador, no restricciones duras del simulador. No equivalen a un sistema de prevencion de colisiones. |
| Ranking de acciones | Define una preferencia experimental del entrenador, no necesariamente la politica de navegacion deseada en el producto. |
### Tres inconsistencias que conviene resolver

A. terminar no deberia confundirse con una accion de movimiento. Propongo separar la condicion terminal de mision de la accion que conduce a ella. Una mision podria terminar porque se alcanzo el objetivo, porque se cancelo o porque se activo una condicion de seguridad; esos resultados no son equivalentes.

B. El ranking puede esconder decisiones de politica. El orden (not mission_complete, -progreso_medio, -alineacion_deg, boundary_violation) prioriza la finalizacion, luego el progreso y la alineacion. Necesitamos conocer la semantica exacta de boundary_violation, la direccion de cada comparacion y el desempate. No asumiria que el ranking actual representa una politica de seguridad.

C. La continuacion comun puede contaminar la evaluacion. Si una accion alcanza la meta pronto, pero la simulacion continua hasta el horizonte maximo, el barco podria alejarse de ella. Hay que definir si el exito se evalua en el instante de llegada, al final del horizonte o mediante ambos criterios. Sin esa definicion, las metricas de progreso y terminacion pueden entrar en conflicto.
## 2. Mapa inicial de intents y slots

Propongo separar intents del usuario, acciones de Timonel y operaciones del controlador. No son necesariamente la misma lista.

El mapa siguiente es una propuesta para la arquitectura futura, no una declaracion de que todas estas acciones esten implementadas.

### 2.1 Intents candidatos

Unidades y condiciones exactas pendientes de formalizar en el contrato comun.

| Intent candidato | Proposito | Slots propuestos | Estado |
| --- | --- | --- | --- |
| navegar_a | Navegar hasta un punto objetivo | meta_x, meta_z [m]; T [m], si la mision lo configura; v_max [kn], opcional | Derivado de ir_a; semantica incompleta |
| fijar_rumbo | Mantener o alcanzar un rumbo absoluto | theta [grados]; horizonte_s [s], si se expone al planificador | Implementado como rumbo; faltan convenciones angulares |
| ajustar_velocidad | Establecer una velocidad objetivo | v_objetivo [kn] | Propuesta; no figura como accion independiente |
| detener | Solicitar la detencion o una reduccion controlada hasta el estado definido como detenido | Sin slots obligatorios; limite temporal opcional | Nuevo; requiere definir que significa "detenido" |
| cancelar_mision | Solicitar que cese la mision actual | motivo, opcional | Nuevo; no implementado |
| consultar_estado | Solicitar posicion, velocidad, rumbo o estado de mision | campos, opcional | Nuevo; no implementado |
| solicitar_aclaracion | Resolver una instruccion ambigua o incompleta | campo_pendiente, pregunta | Capacidad del dialogo, no accion fisica |

Decision arquitectonica recomendada: no incorporar todos estos intents a A3. Para la primera etapa, conservar el alcance minimo necesario para probar la seleccion entre acciones existentes y el umbral variable.

### 2.2 Contrato propuesto para las acciones fisicas

| Accion | Precondiciones | Postcondiciones esperadas |
| --- | --- | --- |
| rumbo(theta, horizonte_s) | Angulo y horizonte validos; estado del barco disponible | El controlador intenta alcanzar el rumbo solicitado durante el horizonte |
| ir_a(meta_x, meta_z, horizonte_s) | Coordenadas validas; meta definida | El barco progresa hacia la meta, sujeto a la dinamica y las restricciones |
| frenar(horizonte_s, sog_objetivo_kn) | Horizonte y velocidad objetivo validos | La velocidad tiende al objetivo; no se presupone que llegue a el dentro del horizonte |
| terminar(meta_x, meta_z, horizonte_s) | Meta y criterio de llegada definidos | Devuelve un estado terminal solo si se satisface el criterio formal de exito |
### 2.3 Restricciones transversales

Estas no deberian ser slots opcionales que el LLM pueda omitir. Son invariantes del sistema, aplicables a todas las acciones:

- Validez estructural: nombre de accion permitido, argumentos obligatorios presentes y tipos correctos.
- Validez fisica: limites de actuadores y comandos compatibles con el modelo.
- Limites del entorno: no atravesar limites definidos como infranqueables.
- Colision: no entrar en contacto con obstaculos clasificados como peligrosos.
- Politica de mision: respetar los criterios de llegada y las condiciones de terminacion.
- Integridad del estado: no ejecutar sobre datos invalidos, caducados o contradictorios sin aplicar la politica de contingencia correspondiente.

Las cuatro primeras requieren implementacion y pruebas. Las dos ultimas tambien necesitan un contrato preciso.

## 3. Organizacion de las fases

Mantendria F1-F4, pero agregaria una F0 de alineacion contractual. Sin ella, un fallo puede atribuirse al modelo cuando en realidad el banco y el simulador estan evaluando reglas diferentes.

### F0

Contrato y baseline.

Unificar el esquema de acciones, los criterios de exito, las unidades y la evaluacion. Sin aprendizaje nuevo ni restricciones fisicas nuevas.

Criterio de salida: banco y simulador coinciden en los casos de referencia.

### F1

Umbral variable.

Introducir T como parametro explicito de la mision y comprobar si Timonel aplica correctamente el criterio de llegada.

Una sola variable nueva; sin composicion de restricciones.

### F2

Composicion de condiciones.

Introducir dos o mas condiciones compatibles, con prioridad y desempate definidos antes del test.

Criterio: cada condicion se respeta y las prioridades se resuelven de forma determinista.

### F3

Seguridad simulada.

Incorporar geometria de obstaculos, limites del mundo y un verificador independiente. Medir violaciones, no solo recompensas o progreso.

El entorno y el oraculo de seguridad deben validarse antes de evaluar al LLM.

### F4

Abstencion y recuperacion.

Añadir un resultado explicito de abstencion ante informacion insuficiente, contradicciones o acciones no autorizadas.

Criterio: no ejecutar acciones invalidas y distinguir abstencion correcta de rechazo innecesario.

Orden recomendado: F0 -> F1 -> F2 -> F3 -> F4, con una salvedad. Si el sistema ya puede ejecutar acciones inseguras, el mecanismo basico de rechazo de comandos invalidos debe existir desde F0; F4 evalua la abstencion como capacidad explicita ante incertidumbre, no como primera barrera de seguridad.

Cada fase debe conservar un conjunto de pruebas de regresion de las fases anteriores. De lo contrario, una mejora en composicion podria ocultar una regresion en el umbral.

## 4. Resolver el conflicto entre T fijo y T variable

Hay tres opciones:

| Opcion | Ventaja | Problema |
| --- | --- | --- |
| A. Mantener T=15 en el simulador y adaptar el banco | Cambio minimo | No permite validar en simulacion la generalizacion a otros umbrales |
| B. Añadir un T configurable a terminar | Hace coincidir los contratos | Puede mezclar configuracion de mision con argumentos de una accion |
| C. Definir T en la configuracion de mision y compartirlo entre banco, entrenador y simulador | Contrato unico, trazable y reutilizable | Requiere definir como se propaga la configuracion |

Recomiendo C. El umbral de llegada pertenece conceptualmente a la mision, no necesariamente a la accion que la declara terminada.

La condicion podria formalizarse asi:

mission_complete <=> d(barco, meta) < T

Esto es solo el criterio geometrico inicial; no presupone que sea el criterio final de exito nautico.

Para A3, el banco debe suministrar un T conocido al sistema y el evaluador independiente debe comprobar el resultado. Si se esta evaluando la capacidad de generalizar a umbrales no vistos, esos umbrales deben reservarse antes de ajustar el modelo.

## 5. Restricciones minimas para F3

No propongo limites nauticos reales sin datos del barco, del entorno y del objetivo de seguridad. Si propongo un escenario de simulacion controlado.

| Restriccion experimental | Implementacion necesaria | Verificacion |
| --- | --- | --- |
| Limite del mundo | Region permitida explicita | Detectar salida de la region en cada paso |
| Obstaculos | Geometrias y radio efectivo del barco | Detectar interseccion entre casco y obstaculo |
| Comandos invalidos | Validador de tipos y rangos | Pruebas negativas con argumentos malformados y fuera de rango |
| Limite de velocidad | Parametro de escenario v_max | Verificar velocidad durante toda la trayectoria |
| Datos no disponibles | Estado de sensores con validez explicita | Comprobar que no se ejecuten acciones que requieran datos ausentes |

Estas restricciones permiten medir cumplimiento en el simulador; no equivalen a demostrar seguridad maritima real. En particular, un limite de velocidad por si solo no garantiza evitar colisiones: para ello importan la velocidad relativa, la capacidad de maniobra, la latencia y la distancia de detencion.

Para cada restriccion debe haber un oraculo de seguridad independiente del LLM. El oraculo registra cada violacion, su instante y el estado previo. El entrenador no debe poder convertir una colision en una accion aceptable simplemente porque esa accion obtuvo mas progreso.

## 6. frenar es un intent o una operacion interna?

Mi propuesta es separar tres conceptos:

- detener: intencion de alto nivel que solicita detener el movimiento segun una definicion formal.
- ajustar_velocidad(v_objetivo): operacion de control que establece una velocidad objetivo.
- frenar: nombre de la implementacion actual, cuya semantica debe verificarse antes de conservarlo en la interfaz publica.

El valor por defecto de 0,3 kn indica que la funcion actual no necesariamente ordena velocidad cero. Por eso no trataria frenar y detener como sinonimos.

Para la navegacion autonoma hacia una meta, la politica de llegada podria solicitar reducir la velocidad segun distancia y estado dinamico. Esa politica deberia vivir inicialmente en el controlador o decisor determinista, no en el LLM.

No hace falta que el Director decida aun que velocidad final es nauticamente apropiada. La arquitectura puede definir ahora como parametrizarla, validarla y evaluarla. El valor concreto y los criterios operativos quedan abiertos.

## 7. Que decide el equipo tecnico y que corresponde al Director

| Decision | Responsable propuesto |
| --- | --- |
| Esquema de JSON, tipos, unidades y validacion | Tecnico |
| Propagar un unico T configurable entre componentes | Tecnico |
| Separar estado terminal de accion fisica | Tecnico, sujeto a verificar la implementacion actual |
| Diseño de pruebas, oraculo y metricas | Tecnico |
| Geometrias sinteticas para pruebas controladas | Tecnico, como parametros experimentales |
| Que significa operacionalmente una llegada exitosa en la mision real | Director |
| Velocidad aceptable de llegada y limites de operacion del barco | Director, con evidencia tecnica |
| Que obstaculos, zonas y condiciones ambientales son peligros reales para el dominio | Director, apoyado por analisis tecnico |
| Que hacer ante perdida de sensores en operacion real | Director define la politica operativa; tecnico implementa y verifica |
| Que acciones puede autorizar Timonel en una futura version | Decision conjunta: dominio, seguridad y arquitectura |

## Propuesta final

Antes de escribir el contrato definitivo de A3, cerraria unicamente estos tres entregables tecnicos:

1. Contrato comun de mision y acciones: esquema, unidades, estado terminal y T configurable.
2. Inventario verificable de seguridad: que controles existen, cuales faltan y como se detecta cada violacion.
3. Protocolo F0/F1: baseline congelado, conjunto de pruebas reservado y criterio de salida.

Despues Claude puede revisar las decisiones tecnicas y sus evidencias. El Director solo necesita intervenir en las cuestiones que realmente dependen de la mision nautica, no en detalles de implementacion que pueden resolverse mediante un contrato consistente.

La regla central es simple: no evaluar si Timonel aprendio una politica cuando todavia no hemos garantizado que el banco, el simulador y el evaluador esten midiendo la misma politica.
