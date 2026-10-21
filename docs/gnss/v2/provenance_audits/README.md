# Trazabilidad mínima V2

## Qué hace la integración de ejecución

`run_all.py` captura una huella de procedencia al empezar una evaluación y, tras escribir `detail.jsonl`, `by_scenario.csv` y `summary.json`, genera `provenance_manifest.json` dentro del directorio de esa corrida. A continuación valida el manifiesto. Si el manifiesto no valida, el proceso termina con código distinto de cero y conserva los resultados escritos y el manifiesto para diagnóstico.

La huella de inicio incluye el commit y el estado Git observables, argumentos de ejecución, entorno Python/plataforma y SHA-256/tamaño de los archivos fuente relevantes. Al finalizar se compara la huella del código para detectar cambios durante la corrida. También se registran las entradas reales referenciadas por `detail.jsonl` y sus hashes, y se comprueba la paridad de fijaciones por escenario/semilla.

Los generadores y `tools/gnss_simulator.py` se registran como código disponible al inicio de la evaluación, pero **no se presentan falsamente como prueba de qué código produjo insumos generados con anterioridad**. Para acreditar el generador realmente usado en el futuro, los propios generadores también deben guardar sus hashes en el momento de producir cada archivo.

## Integridad y límites

- La integración no regenera trayectorias/fijaciones, no altera algoritmos y no incluye hashes por fila/celda.
- Los archivos fuente y de entrada se identifican por SHA-256 y tamaño.
- El manifiesto no se incluye a sí mismo entre sus salidas para evitar autorreferencia.
- Si el código cambia entre la captura de inicio y el final, la validación falla.
- Si falta el hash obligatorio `fixes_sha256`, si no coincide con las fijaciones, si se rompe la paridad o si falta un artefacto, la validación falla.
- La captura registra los bytes de fuente visibles en disco y el estado de Git; no es una atestación criptográfica del código que el intérprete cargó en memoria.
- SHA-256 detecta diferencias respecto de la referencia registrada, pero no prueba autoría o autenticidad por sí solo.
- Un manifiesto retrospectivo de una corrida histórica no debe confundirse con uno de ejecución creado automáticamente al correr el evaluador.

## Pruebas aisladas

```bash
python3 -B docs/gnss/v2/tests/test_provenance.py
```

Las pruebas usan un repositorio temporal sintético y no ejecutan `run_all.py`, ni los generadores ni el benchmark real.

## Validar manualmente un manifiesto

```bash
python3 docs/gnss/v2/eval/provenance.py validate \
  --manifest docs/gnss/v2/results/RUN_ID/provenance_manifest.json
```

Sustituir `RUN_ID` por el nombre concreto del directorio de corrida.

## Corridas históricas

Para las corridas existentes, usar el modo retrospectivo (`create`). La atribución histórica se debe mantener explícitamente como reconstrucción y nunca etiquetarse como captura al inicio de la corrida.
