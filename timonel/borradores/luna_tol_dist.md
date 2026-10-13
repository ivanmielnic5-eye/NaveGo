<!-- ingesta: 2026-10-13 20:19 -->
# BORRADOR — LUNA: tol_dist DEBE LEER DEL CONFIG DE MISION

**Fecha:** 2026-10-13
**Estado:** BORRADOR. Fuera del expediente hasta consolidar.
**Origen:** consulta sobre tol_dist en ir_a_punto.

---

1. tol_dist debe provenir de la MisionConfig, no de etiquetar(). Si
   ambos parametros expresan el mismo criterio, debe existir una unica
   definicion canonica.

2. Pasar el valor explicitamente a ir_a_punto:

   ir_a_punto(b, meta_x, meta_z,
              tol_dist=mision.arrival_distance_threshold.value)

   El nombre del campo es ilustrativo; usar el nombre real del esquema.

3. timonel_python obtiene la configuracion de mision y suministra el
   valor a cada llamada. ir_a_punto no carga archivos ni consulta
   globales. Asi la dependencia queda visible y testeable.

4. Para evitar doble fuente, no basta con compartir la ruta del
   archivo: hay que compartir la misma instancia inmutable de
   configuracion durante toda la evaluacion del contexto. etiquetar()
   y el controlador reciben esa instancia, o valores derivados de
   ella; ambos registran el mismo hash.

5. Si cambia la configuracion, se crea una instancia nueva para la
   siguiente evaluacion. Una corrida en curso nunca relee ni cambia su
   configuracion.

6. Precision sobre el ejemplo: si la llegada se define como
   distancia <= umbral, con tol_dist=15 y T=20 la mision ya considera
   llegada al alcanzar 15 m. El caso problematico es tol_dist=20,
   T=15: la receta podria detenerse antes de satisfacer el criterio de
   mision.

7. Si alguna vez se decide que el controlador y la mision necesitan
   tolerancias diferentes, deben ser dos campos con nombres y
   semanticas distintas, no dos valores accidentalmente divergentes
   del mismo concepto.
