# NAVEGO // COCKPIT — Especificacion PC

Actualizado: 2026-08-19

## Rol de la PC
La PC es el canvas de supervision y construccion.
El celular es el instrumento de operacion y percepcion.
El Cockpit debe ser el puente entre ambos.

## Principio visual
"Hay mucha complejidad debajo, pero el humano solo ve lo necesario."

## Referencias esteticas
Tesla cockpit, instrumento nautico moderno, HUD, estacion de control, consola de nave.

## Estructura conceptual
HEADER, luego ESTADO, luego AREA PRINCIPAL, luego EVIDENCIA, luego DOCK universal.

## Header
NAVEGO en blanco, // COCKPIT en cyan.
Sin subtitulos innecesarios, sin breadcrumbs.
Luces de salud a la derecha.

## Luces de estado
GNSS, SERVIDOR, TUNEL, METRO.
Verde: operativo.
Amarillo: degradado o en observacion.
Rojo: requiere intervencion.
Gris: no verificado o no disponible.
Deben ser instrumentos perifericos, no tarjetas grandes.

## Material de paneles
Fondo oscuro azul negro profundo.
Superficie azul marino muy oscura.
Borde cyan de baja opacidad.
Separacion por espacio, contraste y borde, no por sombras.
Radios de panel: 20 a 28 px.
Radios de controles pequenos: 12 a 18 px.
Radio del dock: 24 a 32 px.

## Paleta de color
Base: negro azul profundo.
Superficie: azul petroleo o navy.
Texto principal: blanco frio.
Texto secundario: azul grisaceo.
Acento: cyan electrico.
Estados: verde, amarillo, rojo.
No agregar colores arbitrarios.

## Tipografia
Moderna, geometrica, altamente legible.
Titulo: 28 a 36 px.
Seccion: 18 a 22 px.
Dato principal: 32 a 48 px.
Informacion secundaria: 12 a 15 px.
Metadato: 10 a 12 px.
Reservar mayusculas para estados, etiquetas, comandos y titulos cortos.

## Jerarquia de informacion
Nivel 1 Urgente: solo lo que requiere intervencion humana.
Nivel 2 Importante: estado actual, tarea activa, evidencia.
Nivel 3 Accesorio: logs, timestamps, metadatos.

## Area principal
Es dinamica y cambia segun el modulo activo.
El header y el dock permanecen fijos.
La estructura es: contexto fijo mas contenido variable mas control fijo.

## Dock
Cinco modulos: ESTADO, TRABAJO, EVIDENCIA, ARCHIVOS, ACCION.
Icono grande, etiqueta pequena, estado activo visible.

## Iconografia
Line icons, trazo uniforme, geometria simple.
ESTADO: pulso.
TRABAJO: laboratorio o proceso.
EVIDENCIA: ojo.
ARCHIVOS: carpeta.
ACCION: microfono.

## Estados de los botones
Normal, hover, presionado, activo, deshabilitado, advertencia, error.
Respuesta sutil, evitar animaciones permanentes.

## Espacio negativo
En pantalla grande, mas espacio vacio, no mas informacion.
La sensacion debe ser: "puedo respirar dentro de esta interfaz".

## Responsive
La PC es el canvas principal.
El celular es una version comprimida de la misma gramatica.
La estructura conceptual se mantiene.

## Voz
El boton ACCION queda preparado para voz, pero sin implementar todavia.
La voz sera otra entrada al mismo sistema, no una interfaz paralela.

## Entregables antes de implementar
1. Wireframe conceptual.
2. Design system.
3. Interaction map.
4. Criterios de implementacion.

## Percepcion final buscada
En 2 segundos el usuario debe poder responder:
Que esta pasando?
Hay algun problema?
En que estamos trabajando?
Que esta comprobado?
Que puedo hacer ahora?

La interfaz debe sentirse como: "el sistema esta bajo control".
