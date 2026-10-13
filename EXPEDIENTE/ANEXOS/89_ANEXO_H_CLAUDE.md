# ANEXO H — CLAUDE / REFORMULACION CON EL ANEXO G A LA VISTA

**Fecha:** 2026-10-13
**Origen:** segunda consulta a Claude, con el texto completo del anexo G (Luna).
**Contenido:** reformulacion de la respuesta anterior de Claude tras ver el anexo G.

---

# Reformulacion con el anexo G a la vista

Con el texto completo, mi balance es: Luna cubre mas de lo que yo suponia
en cobertura de dimensiones, conflicto entre restricciones y limitaciones
documentales. Mis aportes se concentran en la comparacion justa (la
asimetria estructurado-vs-texto), el techo estructural, la economia y el
alcance de la conclusion. Corrijo ademas dos objeciones mias que no se
sostenian.

## Balance por categoria

| Categoria | Contenido |
|---|---|
| Cambia de lo que dije | - Obstaculo: mi objecion de "geometria 2D" no se sostiene. El contrato C del anexo es una condicion con prioridad de seguridad, representable con un escalar. Lo difiero por economia y por etapas, no por geometria. Su aporte genuino es el conflicto entre restricciones. - Lenguaje natural: no esta ausente. Luna lo cubre como robustez (parafrasis y criterio de "cambios injustificados de accion"). Lo que no cubre es el eje comparativo contra el Python. - Abstencion: su contrato D esta especificado por contrato (se dice que hacer), asi que es aceptable como familia; la version de su seccion 5D ("no inventar una resolucion") es juicio y sigue separada. - Cierre de A2: la extrapolacion (T=6 y 32 al 100%) y la concordancia de generacion en 200 casos ya figuran; ya no faltan. - Probe: no es independiente de Luna; esta contenido en su familia 2. - Lazo cerrado: ya esta en su matriz de capacidades ("Planificacion y control"). Lo saco de mis "puntos ciegos". |
| Se mantiene | - P-text e hibrido como brazos adicionales; su sistema B equivale a mi P-struct. - H1b decisional no es testeable en familias deterministas (P-struct = 100% por construccion). - Criterio de interfaz y esfuerzo exploratorio. - Pendientes de A2: AUC de la base (0,310 < azar), numero de semillas, rango de d (aprox 36 m max.). - Tension SFT vs. flexibilidad y definicion de que es "el LLM". - Diseno secuencial y regla de tres. |
| Ya cubierto por Luna (no duplicar) | Separacion H1a/H1b; baseline configurable en vez de if; arbol; invariancia y estratos de A2; contrafactuales y parafrasis; particion por combinaciones, no por filas; matriz de capacidades (incluye conocimiento nautico); tres conclusiones posibles; clasificacion de limitaciones; cautela causal A1->A2 |
| Aportes mios que Luna no tenia | - Brazo P-text y hibrido (la asimetria de parseo: su B recibe el contrato ya estructurado). - Techo estructural de H1b decisional. - Regla de tres, base de sus 300 por familia. - Probe por cuadrante como etapa 0. - Alcance de la conclusion al artefacto. - Rango de d, AUC de la base, semillas. - Brazo techo zero-shot grande. - Protocolo de esfuerzo (ediciones de codigo). - Criterios numericos por familia. |
| Aportes de Luna que yo no tenia | - Conflicto texto-datos (su prueba C): un texto incidental que sugiere la accion contraria. - Contratos contradictorios o incompletos. - Errores criticos como eje de seguridad. - Matriz de capacidades. - Criterio "cero errores criticos". |

## Donde discrepo con Luna (ya con su texto a la vista)

1. El umbral global >=95% con limite inferior >=90% es laxo. A2 saco 100%
   en una regla determinista y explicita; ese umbral tolera aprox 60
   errores en 1200. Y "ninguna familia oculta tras el promedio" no trae
   cifra. Propongo >=0,99 por familia con limite inferior de Wilson >=0,97
   (n=300) para sostener H1a, y dejar el 95/90 como compuerta de cribado
   de la etapa 1.

2. "Error critico" nunca se define. Propongo: declarar terminar cuando el
   contrato lo prohibe (falso terminar).

3. "Cero errores criticos observados" no es una cota. Con n=300 por
   familia, cero errores acota el error a aprox 1% (95%); eso es lo que
   hay que preregistrar.

4. Su sistema B no tiene parser. Reconoce que recibe "una especificacion
   estructurada equivalente", pero no trata la asimetria con el LLM, que
   lee texto. Sin P-text, H1b-interfaz no se mide.

5. "Sin reentrenamiento" es ambiguo. No dice que SFT es el sistema A. Si
   es el adaptador de A2 (solo umbrales), las familias 2-4 son familias
   nuevas, y es probable (inferencia mia) que lo ignore. Y su conclusion 3
   ("el LLM no demuestra adaptacion") se atribuiria a "el LLM" cuando solo
   habria fallado ese artefacto. Hay que preregistrar el alcance.

6. Su 5D (sin clausula de abstencion) es juicio, no seguimiento de
   contrato; no lo mezclaria con las familias especificadas.

## Respuestas a las 5 preguntas

1. Cambia algo de mis secciones 2, 4 y 6?
   - Sec. 2: si, lo indicado en la tabla (obstaculo, lenguaje, abstencion).
   - Sec. 4: se mantiene, y se refuerza: Luna dice que 1200 es "propuesta
     inicial, no validada". La regla de tres le da base si la afirmacion
     es "error <=1% por familia".
   - Sec. 6: se mantiene. Luna deja "metrica primaria de ventaja y margen"
     sin definir y "coste y tiempo de adaptacion" sin protocolo; mi
     propuesta (criterio de interfaz con P-text, esfuerzo exploratorio)
     las operacionaliza.

2. P-struct / P-text / Hibrido siguen? Si. Luna cubre P-struct (su B) y
   el arbol. No cubre P-text ni el hibrido, y son los que hacen medible
   H1b.

3. A3-nucleo (800 casos) sigue valiendo? Ya no como alternativa, sino
   como etapa 1 de su protocolo con compuertas. Reconciliado:
   - Etapa 0 (sin entrenar): cierre de A2 y probe por cuadrante con el
     adaptador de A2.
   - Etapa 1: F1+F2, factor de formulacion, brazos P-struct/P-text/arbol/
     LLM; 600 casos + probe 200. Compuerta: cribado 95/90 y cero errores
     criticos.
   - Etapa 2 (solo si pasa): F3 (prioridad de seguridad) con prueba de
     conflicto texto-datos, hibrido, 3 semillas, criterios por familia.
   - Etapa 3 (aparte): F4 (abstencion especificada por contrato) con 3
     acciones, y familia retenida.
   - Costo total aprox el de Luna (1200 mas el probe), pero con corte
     temprano si algo falla.

4. El probe sigue siendo "la prueba mas directa que Luna no propuso"?
   Corrijo la frase. Luna no lo aisla, pero esta contenido en su familia
   2. Sigue valiendo como etapa 0 de cribado (sin entrenar, por cuadrante)
   y como diagnostico: aislado por cuadrante dice por que falla (ignora
   la clausula), cosa que un promedio por familia no muestra.

5. Cambia mi seccion 7?
   - Se mantiene: tension SFT vs. flexibilidad, rango de d, brazo techo.
   - Se elimina: lazo cerrado (lo cubre Luna).
   - Se agrega a partir del anexo:
     - Error critico indefinido y criterios sin cifras por familia.
     - Alcance de la conclusion al artefacto, no a "los LLM".
     - La prueba C de Luna es un riesgo, no solo una prueba: un LLM puede
       ser influido por texto incidental y el motor Python es inmune. Es
       la superficie de ataque de un contrato en lenguaje natural y
       deberia pesar en cualquier recomendacion de uso real.