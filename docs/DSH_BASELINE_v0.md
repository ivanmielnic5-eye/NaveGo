# DSH Baseline v0

**Fecha:** 18 sep 2026
**Estado:** VERIFICADO

## Objetivo

Demostrar autonomía operativa de DSH sobre un workspace real,
eliminando la necesidad de transportar manualmente archivos y
resultados entre el agente y el entorno de desarrollo.

## Ensayos verificados

### Ensayo 01 — Lectura autónoma
DSH + DeepSeek API leyó un archivo real del workspace y respondió
sobre su contenido sin intervención humana para proporcionar el archivo.
Resultado: VERIFICADO

### Ensayo 02 — Edición controlada
DSH localizó y modificó un archivo del workspace según una instrucción
determinada, sin modificar archivos fuera del alcance indicado.
Resultado: VERIFICADO

### Ensayo 03 — Ciclo autónomo completo
DSH ejecutó un ciclo: ejecutar, observar, diagnosticar, modificar,
volver a ejecutar, verificar, reportar.
Resultado: VERIFICADO

## Stack

- DSH: 0.1.5-rc.1
- DeepSeek API (cuenta con crédito cargado)
- Perfil headless con baseURL https://api.deepseek.com
- Ollama disponible como infraestructura local alternativa

## Conclusión

Baseline v0 de autonomía operativa reconstruido y verificado.

La capacidad demostrada no depende exclusivamente de la potencia
del modelo. El elemento fundamental es el acceso del agente al
entorno real y la posibilidad de ejecutar, observar y modificar.

## Próxima etapa

Experimentación controlada sobre un branch de NaveGo, manteniendo:
- evidencia de cada operación
- revisión humana
- reversibilidad
- ausencia de modificaciones directas sobre main
