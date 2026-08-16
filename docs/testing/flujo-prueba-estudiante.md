# Flujo de prueba — Estudiante / Asistente de chat

Checklist manual para probar el chat, los modos y el tutor de material de estudio como
estudiante. Requiere haber corrido primero `flujo-prueba-coordinador.md` (o al menos haber
subido material a **Algebra Lineal**, **Estadistica** e **Ingles 3**, las tres materias del
semestre 5 del estudiante de prueba).

## 0. Iniciar sesión

<http://localhost:3000> con:

| Correo | Contraseña |
|---|---|
| `jose.hernandez540@pascualbravo.edu.co` | `Estudiante#2026` |

Estudiante matriculado en Ingeniería de Software, semestre 5.

## 1. Asistente General de Carrera

- [ ] Con **General de Carrera** seleccionado en la barra lateral, preguntar algo de malla
      curricular: *"¿Qué materias veo este semestre?"* — debe responder con las materias del
      semestre 5 sin pedir el semestre ni el programa (el sistema ya los conoce).
- [ ] Preguntar por prerrequisitos de una materia futura, ej. *"¿Qué necesito para ver
      Arquitectura de Software?"*.
- [ ] Confirmar que **no aparece el selector de modo** (Consulta/Estudio/Práctica/Examen/
      Resumen) en el header — el selector de modo es exclusivo de un asistente por materia.

## 2. Cambiar a un asistente por materia

- [ ] Seleccionar **Algebra Lineal** en la barra lateral. Debe abrirse una conversación nueva
      (cambiar de asistente no comparte contexto).
- [ ] Confirmar que ahora **sí aparece** el selector de modo, en Consulta por defecto.
- [ ] Preguntar algo genérico de la materia: *"¿De qué trata esta materia?"* — no debe pedir
      el nombre de la materia ni el semestre.

## 3. Aislamiento entre materias (regresión del bug original)

Esta es la prueba más importante — un bug de producción real motivó todo este trabajo.

- [ ] Estando en el asistente **Algebra Lineal**, preguntar algo que solo tendría sentido en
      **Ingles 3**, ej.: *"Explícame el past perfect"* o *"dame un ejercicio de inglés"*.
- [ ] El asistente debe **rechazar amablemente** el tema (indicar que no corresponde a este
      asistente y sugerir cambiar de materia en la barra lateral) — **nunca** debe responder
      con contenido real de Inglés 3, aunque haya material de Inglés subido por coordinación.
- [ ] Repetir nombrando la materia explícitamente, ej.: *"búscame algo de Inglés 3 sobre
      verbos"* — tampoco debe devolver contenido de Inglés 3 (esa materia no es prerrequisito
      de Álgebra Lineal). Si pide un ejercicio de un prerrequisito real de la materia activa
      (revisar la malla para saber cuál), sí puede buscarlo ahí — esa es la única excepción
      permitida.

## 4. Modo Estudio

- [ ] En **Algebra Lineal**, cambiar el modo a **Estudio** y pedir que explique un concepto
      del PDF subido (ej. *"explícame qué es un espacio vectorial"* si subiste ese capítulo).
- [ ] La respuesta debe ser paso a paso, construyendo desde lo básico, no solo la respuesta
      corta.

## 5. Modo Práctica — tarjeta de ejercicio

- [ ] Cambiar el modo a **Práctica** y pedir un ejercicio del tema subido (ej. *"dame un
      ejercicio de matrices"*).
- [ ] Debe aparecer una **tarjeta de ejercicio** (no el panel genérico de "llamada a
      herramienta") con texto real extraído del PDF subido — nunca un ejercicio inventado.
- [ ] Escribir una respuesta en el cuadro de texto libre y enviarla — el asistente debe dar
      retroalimentación sobre si la respuesta es correcta, y explicar el razonamiento paso a
      paso si es un ejercicio matemático.
- [ ] Si el PDF subido no tiene ningún ejercicio reconocible, la tarjeta debe mostrar un
      mensaje honesto de "no encontré un ejercicio", nunca inventar uno.

## 6. Modo Examen

- [ ] Cambiar a **Examen**, indicar un tema (*"quiero practicar para el examen de matrices"*).
      Debe buscar ejercicios reales uno a la vez y retroalimentar cada respuesta antes de
      pasar al siguiente — mismo mecanismo de tarjeta que Práctica.

## 7. Modo Resumen

- [ ] Cambiar a **Resumen** y pedir un resumen de un tema. Debe entregarse como lista de
      puntos clave tipo hoja de estudio, no como conversación.

## 8. Cambiar de asistente no debe romper nada (regresión reciente)

- [ ] Estando en **Algebra Lineal** en modo **Examen**, hacer clic en **General de Carrera**
      en la barra lateral.
- [ ] Preguntar algo de malla curricular ahí. Debe responder normalmente — **no** debe
      intentar usar herramientas de búsqueda de material ni caer en la respuesta genérica de
      "no pude completar tu solicitud". (Si esto falla, es una regresión del fix de modo
      "Examen que se queda pegado al cambiar de asistente".)
- [ ] Volver a **Algebra Lineal** — el modo debe estar de nuevo en **Consulta** por defecto
      (una conversación nueva siempre reinicia en Consulta), no en Examen.

## 9. Persistencia y transparencia

- [ ] Recargar la página (F5) en medio de una conversación — la conversación debe seguir
      visible en "Recientes" en la barra lateral y poder reabrirse con su historial completo.
- [ ] Al reabrir una conversación vieja de Práctica/Examen desde el historial, sus resultados
      de búsqueda de material vuelven a mostrarse como el panel genérico (no como tarjeta de
      ejercicio) porque el modo se reinicia a Consulta al reabrir — comportamiento esperado,
      no es un bug.
- [ ] Abrir el panel de transparencia de una respuesta con búsqueda de material (icono de
      herramienta) — debe mostrar cuántos fragmentos encontró, no un número fijo en 1 sin
      importar cuántos resultados hubo.
- [ ] Dar feedback (pulgar arriba/abajo) a una respuesta del asistente.
- [ ] Confirmar que el texto del asistente se ve con formato (negritas, listas) y no con
      asteriscos literales.
