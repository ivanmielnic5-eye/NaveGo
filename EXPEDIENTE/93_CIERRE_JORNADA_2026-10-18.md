# CIERRE DE JORNADA — NAVEGO (2026-10-18)

**Fecha:** 2026-10-18
**Estado del repositorio:** HEAD en `4123481` (documentación), con cambios locales en `tasks/backgroundLocationTask.ts` y el módulo nativo `modules/navego-native` sin commitear.
**Estado de la app en el celular:** Debug build instalado. Abre, pero con fallos de enganche y fantasmas.

## 1. Lo que se resolvió hoy (Hechos)

- **Crash de apertura solucionado:** La app se quedaba en la pantalla blanca por un error de empaquetado (`ClassNotFoundException: SplashScreenManager`). El `gradlew clean` y recompilación solucionaron ese punto.
- **Módulo nativo (Kotlin) instalado:** El puente JS-Kotlin no fue verificado aún porque la app queda atrapada en el arranque antes de ejecutar la lógica de negocio.
- **Base de datos con bloqueos:** En los logs se observaron errores en bucle (`database is locked`) del orquestador (JS) al intentar procesar fixes.

## 2. Síntomas reportados por el Director

- **El primer trayecto no engancha:** Al abrir la app y darle a INICIAR, el HUD no se conecta con el track ni con la distancia. Hay que finalizar y volver a iniciar para que tome los datos.
- **Movimientos fantasmas:** El sistema sigue sumando metros y generando coordenadas de la nada, sin origen identificado.

## 3. Arquitectura acordada con Luna y Claude (Plan a futuro)

1. **`capture.db` (Kotlin):** El servicio nativo escribe los GPS crudos en su propia base, sin depender de JS.
2. **`navego.db` (JS):** La app lee esa base de captura, procesa la lógica (Kalman, hash, distancia) y la guarda como verdad oficial.
3. **Cero escritores duales:** Se eliminan los bloqueos al tener un único escritor por archivo.
4. **Track Honesto:** Si hay un hueco, el track se dibuja negro/amarillo discontinuo y no suma distancia.

## 4. Hipótesis sobre los movimientos fantasmas

- **Hipótesis A:** La Task de background actual (JS) y el nuevo servicio Kotlin (si está capturando) escriben en paralelo o el polling lee puntos de una sesión vieja `ACTIVE`.
- **Hipótesis B:** El GPS rebota bajo techo y `processFix` acepta esos puntos como válidos sin un umbral ajustado.

## 5. Próximos pasos

1. Aislar el fantasma: test con app cerrada, verificar si hay puntos en la base sin haber tocado INICIAR.
2. Terminar el puente JS-Kotlin para que la app lea datos de `capture.db` y matar la Task vieja de JS.
3. Revisar el `useEffect` de inicialización del `useNaveGoTracker.ts` para el bug del primer trayecto.
