# BORRADOR — LUNA: CRITERIO DE CONTAMINACION (CORRECCION)

**Fecha:** 2026-10-13
**Estado:** BORRADOR.
**Origen:** correccion a criterio demasiado estricto sobre
contaminacion de F-held.

---

DeepSeek esta aplicando un criterio de contaminacion demasiado
amplio. Distingo cuatro cosas:

1. Conocer el proyecto y su hipotesis. No descalifica al autor. Para
   generar formulaciones validas, el autor necesariamente debe
   conocer la regla abstracta: d < T AND v <= v_max.

2. Haber visto las formulaciones concretas de F_train/F_dev, sus
   etiquetas o el analisis de errores. Esto si compromete la
   independencia.

3. Conocer resultados agregados (ej. P-text=100% en A3). No equivale
   a haber visto items retenidos, pero puede sesgar el diseno.
   Registrarlo.

4. Usar un LLM en sesion nueva. Que el mismo modelo se haya usado en
   otras conversaciones no implica que la sesion nueva reciba ese
   contexto. La independencia contextual depende de no transferir
   historial, memoria, archivos ni recuperacion del proyecto.

La elegibilidad debe decidirse por exposicion efectiva y
procedimiento, no por identidad del investigador, proveedor o
modelo.

Sobre el CEO: si no vio las formulaciones especificas ni los
analisis de errores, no corresponde declararlo contaminado
automaticamente. Su desconocimiento tecnico tampoco demuestra
independencia; lo relevante es que materiales vio.

Sobre LLM en sesion limpia: no descartarlo solo porque comparte
familia con una instancia previa. Aceptarlo como autor con
independencia contextual documentada, siempre que la sesion no
reciba informacion previa. No afirmar independencia absoluta del
modelo ni ausencia de exposicion en su entrenamiento.

Propuesta: auditar que vio cada candidato antes de resignarse a
F-held exploratorio. Si existe una via de generacion aislada, con
consigna sellada, sin items ni errores previos y con validacion
ciega, evaluar si satisface los requisitos confirmatorios definidos
de antemano.

No confundir rigor con exigir una pureza imposible de demostrar.
Definir que independencia necesita medir F-held, que amenazas la
comprometen y cuales son limitaciones declarables.
