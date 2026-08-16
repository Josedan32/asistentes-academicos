# Handoff: Asistente académico con agente — Institución Universitaria Pascual Bravo

## Overview
Plataforma web con dos roles. Los **estudiantes** conversan con un agente LLM (Ollama, modelo ~3B) que responde consultando la base de datos académica mediante *tool calling*: malla curricular, materias, créditos y prerrequisitos. La **coordinación** administra carreras, materias y la malla de cada carrera.

Seis pantallas, mínimas a propósito:

| # | Pantalla | Rol |
|---|----------|-----|
| 1 | Login | ambos (redirige según rol) |
| 2 | Registro de estudiante | público |
| 3 | Chat | estudiante |
| 4 | Carreras | coordinación |
| 5 | Materias | coordinación |
| 6 | Malla curricular | coordinación |

La pantalla 3 es el producto. La 6 es la única de administración con diseño real.

## About the Design Files
Los archivos en `design/` son **referencias de diseño escritas en HTML** — prototipos que muestran aspecto y comportamiento esperados, no código de producción para copiar.

La tarea es **recrear estas pantallas en el stack objetivo**: Next.js 15 (App Router) + React 19 + TypeScript + Tailwind v4 + shadcn/ui, usando los patrones y componentes ya establecidos en ese proyecto. Los estilos del prototipo están escritos inline; tradúcelos a clases de Tailwind y a componentes shadcn (`Button`, `Input`, `Select`, `Table`, `Dialog`, `Sheet`, `Checkbox`, `Textarea`, `Badge`, `Collapsible`).

Cada archivo `.dc.html` se abre directamente en un navegador. La lógica de estado vive en la etiqueta `<script>` al final de cada archivo.

## Fidelity
**Alta fidelidad.** Colores, tipografía, espaciado y estados son definitivos. Recrear la UI con precisión, mapeando los valores exactos de la sección Design Tokens al `@theme` de Tailwind v4.

---

## Screens / Views

### 1 · Login
**Propósito:** entrada única para estudiantes y coordinación. El backend redirige según el rol del usuario autenticado.

**Layout:** contenedor 1440×900, `grid-template-columns: 1fr 1fr`.
- **Panel izquierdo** — fondo `#0B2140`, padding 64px, columna con `justify-content: space-between`.
  - Logo sobre placa blanca (`border-radius: 8px`, padding 14px 18px, ancho `fit-content`), imagen a 44px de alto.
  - Bloque central: eyebrow "ASISTENTE ACADÉMICO" (600 12px, `letter-spacing: .18em`, uppercase, `#6E9BC7`); titular 700 46px/1.08 blanco, `letter-spacing: -.01em`, máx. 440px: "Un agente que consulta tu malla, no que la inventa."; párrafo 400 17px/1.6 `#AFC2D6`.
  - Pie: "Facultad de Ingeniería · Medellín", 400 13px `#6E8AAB`.
- **Panel derecho** — fondo `#F7F8FA`, centrado, formulario de 400px máx., `gap: 26px`.
  - H2 "Iniciar sesión" 700 30px/1.1 `#0B2140`; subtítulo 400 15px/1.5 `#6B7684`.
  - Campos correo y contraseña: label 600 13px `#3B4757`, input alto 46px, borde `#D3D9E0`, radio 8px, padding lateral 14px, texto 15px. Foco: borde `#1D5B96` + `box-shadow: 0 0 0 3px rgba(29,91,150,.14)`.
  - Fila: checkbox "Mantener sesión" (accent `#1D5B96`) + enlace "Olvidé mi contraseña".
  - Botón primario: alto 48px, ancho completo, `#0B2140`, texto blanco 600 15px, radio 8px. Hover `#12345F`.
  - Separador 1px `#E2E5EA` y enlace a registro.

### 2 · Registro de estudiante
**Propósito:** alta pública. **Carrera y semestre no son campos de formulario cualesquiera: son el contexto que alimenta al agente** — determinan qué materias ve el estudiante y qué asistentes se le habilitan.

**Layout:** cabecera blanca de 68px (logo 30px + enlace a login), cuerpo centrado de 720px con `gap: 28px`, scroll vertical.

**Bloque A — Datos personales** (tarjeta blanca, borde `#E2E5EA`, radio 12px, padding 28px):
grid de 2 columnas, `gap: 16px`. Campos: Nombres, Apellidos, Documento, Correo institucional, Contraseña, Confirmar contraseña. Inputs de 44px, mismo estilo que login.

**Bloque B — Contexto académico** (tarjeta destacada: borde `#C7D6E6`, `box-shadow: 0 1px 0 #1D5B96 inset, 0 0 0 3px rgba(29,91,150,.05)`):
- Encabezado: "CONTEXTO ACADÉMICO" en `#1D5B96` + nota derecha "Define las materias que verá tu asistente".
- `Select` de carrera (44px, ancho completo).
- Semestre: fila de 10 botones de 52×44px, radio 8px. No seleccionado: borde `#D3D9E0`, texto `#3B4757`. Seleccionado: fondo y borde `#0B2140`, texto blanco 600.
- Aviso de resumen: fondo `#F2F6FA`, radio 8px, padding 14px 16px, disco azul de 22px con "i" y texto 400 14px/1.5 que enumera en negrita los asistentes resultantes. **Este texto se calcula en cliente al cambiar carrera/semestre** (consulta a la malla).

**Pie:** checkbox de tratamiento de datos (a la izquierda, máx. 420px) + botón "Crear cuenta" (48px, `#0B2140`).

### 3 · Chat  ← el 80% del esfuerzo de diseño
**Layout:** 1440×900, `grid-template-columns: 288px 1fr; grid-template-rows: 100%`, `overflow: hidden`. Ambas columnas llevan `min-height: 0`.

**Barra lateral** (`#0B2140`, columna flex, `overflow: hidden`):
1. Placa blanca con logo (26px) — `flex: 0 0 auto`.
2. Botón "+ Nueva conversación": alto 42px, fondo `#12345F`, borde `#2C4E78`, radio 8px, hover `#1A4374`.
3. **Selector de asistente** — `flex: 0 0 auto`:
   - "General de Carrera" activo: fondo `#1D5B96`, punto verde `#7FD1C1` de 7px, texto blanco 600 14px.
   - Subtítulo "MATERIAS · SEMESTRE 5" (600 11px, `#5F82AC`).
   - Una fila por materia del semestre del estudiante: punto `#3F6693`, texto `#C6D5E6` 400 14px, hover `#12345F`.
   - Nota al pie: "Cambiar de asistente abre una conversación nueva. No se comparte contexto entre materias." (400 12px `#5F82AC`).
4. Divisor 1px `#1B375C`.
5. **Recientes** — `flex: 1 1 0; min-height: 0; overflow: auto`. Cada ítem: título en una línea con elipsis + metadato "asistente · fecha". Activo: fondo `#12345F`.
6. Pie de usuario — `flex: 0 0 auto`, borde superior `#1B375C`, avatar circular 34px `#1D5B96` con iniciales.

**Encabezado** (66px, blanco, borde inferior `#E2E5EA`): cuadro 34px `#0B2140` con iniciales del asistente + nombre del asistente activo (600 15px) + línea de contexto "Ingeniería en Software · malla 2024 · llama3.2:3b" (400 12.5px `#6B7684`). El estudiante siempre debe saber a quién le habla. A la derecha, en el prototipo, un `select` de estado que **existe solo para la demo — no se implementa**.

**Hilo de mensajes:** ancho máximo 800px centrado, padding 28px 24px, `gap: 22px`.
- **Mensaje de usuario:** alineado a la derecha, máx. 78%, fondo `#0B2140`, texto blanco 400 15.5px/1.55, radio `14px 14px 4px 14px`, padding 13px 17px.
- **Mensaje del asistente:** avatar cuadrado 32px + columna. Burbuja blanca, borde `#E2E5EA`, radio `14px 14px 14px 4px`, padding 16px 18px, texto `#233240`.

**Panel de herramientas (el diferenciador — visible siempre, no detrás de un flag de debug):**
Se renderiza una tarjeta por llamada a herramienta, ANTES de la burbuja de respuesta.
- Cabecera plegada (clic para alternar): fondo `#F3F8FC`, borde `#CBDCEA`, radio 10px, padding 11px 14px. Contiene: icono ⚙ `#1D5B96`; descripción en monoespaciada 500 13.5px `#0F3E68` con elipsis (p. ej. `Consultando prerrequisitos de "Base de Datos 2"`); píldora de duración (`0.42 s`, fondo `#E3EEF7`); enlace "ver detalle ▾" / "ocultar detalle ▴" `#1D5B96`.
- Detalle expandido: fondo blanco, borde superior `#DCE8F2`, padding 14px, tres bloques con etiqueta 600 10.5px uppercase `#9AA3AE`:
  1. **Herramienta** — nombre en monoespaciada (`obtener_prerrequisitos`).
  2. **Argumentos** — `<pre>` fondo `#0B2140`, texto `#C6D5E6`, 12.5px/1.6, radio 7px.
  3. **Resultado** — `<pre>` fondo `#F5F7F9`, borde `#E2E5EA`, texto `#233240`.
- Bajo la respuesta: línea de metadatos 400 12.5px `#9AA3AE` — "2 herramientas · 3.4 s · 2 fuentes de la base de datos".

**Feedback por mensaje** (en cada respuesta del asistente): botones 👍 / 👎 de 32×32px (borde `#E2E5EA`, radio 7px; hover 👍 `#1D5B96`, 👎 `#C2603F`) y "Copiar". Al pulsar 👎 (o 👍) se despliega una tarjeta con `textarea` opcional "¿Qué le faltó a esta respuesta?" y botones "Omitir" / "Enviar comentario". **Persistir en base de datos desde la fase 1**: es el conjunto etiquetado para la fase 3, y añadirlo después implica perder todas las interacciones previas.

**Entrada:** contenedor blanco, borde `#D3D9E0`, radio 12px, padding 12px 14px; `textarea` sin borde que crece hasta 120px; botón circular-cuadrado 40px. En reposo: `↑` sobre `#0B2140`. Mientras responde: botón de detener `■` sobre `#A9502F` y textarea deshabilitada. Nota legal centrada abajo, 400 12px `#9AA3AE`.

#### Estados obligatorios de la pantalla 3
Todos se renderizan sobre la entrada, con el mismo ancho de 800px.

| Estado | Cuándo | Tratamiento visual |
|---|---|---|
| **Cargando modelo** | primera petición tras inactividad | Franja azul (`#F3F8FC` / borde `#CBDCEA`): spinner 16px, título "Cargando el modelo en memoria", texto "Primera consulta tras un rato de inactividad. Suele tardar entre 10 y 30 segundos." y barra de progreso 120×5px. Sin esto, el usuario cree que se rompió. |
| **Pensando / usando herramienta** | durante el loop del agente | Misma franja azul: ⚙ pulsante, "Usando herramienta · `nombre_tool`", explicación de que puede haber segundos sin tokens, y botón **Detener** (borde `#C2603F`). |
| **En cola** | otra inferencia ocupa la GPU | Franja ámbar (`#FBF7EA` / borde `#E7DCB8`): disco `#B79322` con la posición, "En cola · segundo lugar", estimación de espera y botón Cancelar. El semáforo de GPU bloquea; hay que decirlo, no dejar un spinner mudo. |
| **Modelo no disponible** | Ollama caído | Franja roja (`#FBF3F0` / borde `#E6C6B9`): mensaje accionable — qué pasó, que las conversaciones previas siguen legibles, y botones "Reintentar" y "Avisar a coordinación". Nunca "Error 500". El botón de envío pasa a `#C2CAD4`. |
| **Sin datos** | la herramienta no devuelve filas | Tarjeta de herramienta con píldora ámbar "0 filas" y respuesta legítima: "No tengo esa información…" + qué sí puede consultar + sugerencia alternativa. Es éxito, no fallo: mantiene 👍/👎. |
| **Vacío** | conversación nueva | Avatar 56px, saludo "Hola, {nombre}." (700 26px), párrafo de capacidades y **grid 2×2 de 4 preguntas sugeridas** (tarjetas blancas, borde `#E2E5EA`, radio 10px, hover borde `#1D5B96` + fondo `#F2F6FA`). Con un modelo 3B, guiar la primera pregunta mejora mucho el resultado. |

### 4 · Carreras (deliberadamente aburrida)
**Layout:** `grid-template-columns: 236px 1fr`. Barra lateral navy de coordinación (logo + etiqueta "COORDINACIÓN" + tres ítems: Carreras / Materias / Malla curricular; activo `#1D5B96`).

**Contenido:** cabecera de 76px con H1 "Carreras" (700 22px), contador "4 programas activos" y botón "Nueva carrera". Filtros: input de búsqueda 280px + `select` de estado, ambos de 38px. Tabla en tarjeta blanca (borde `#E2E5EA`, radio 10px):
- `thead` fondo `#F5F7F9`, celdas 600 12px uppercase `#6B7684`, `letter-spacing: .08em`.
- Columnas: Código (monoespaciada), Nombre (500), Semestres, Materias, Estado (badge: Activa `#E7F1EA`/`#2C6544`; Inactiva `#F1F2F4`/`#6B7684`), acciones ("Malla", "Editar").
- Filas 13px 18px, separador `#EEF1F4`.

**Modal crear/editar** (`Dialog`, 480px, radio 12px, padding 26px, overlay `rgba(11,33,64,.45)`): Nombre, Código, Semestres, checkbox "Carrera activa", botones Cancelar / Guardar.

### 5 · Materias (deliberadamente aburrida)
Misma estructura que Carreras. Subtítulo: "Catálogo global · una materia puede pertenecer a varias carreras". **Las materias son independientes de la carrera**; la relación materia↔carrera↔semestre vive en la malla.

Filtros: búsqueda 300px, `select` de área, `select` "Usada en cualquier carrera / Sin asignar a ninguna malla".
Columnas: Código, Materia, Área, Créditos, En mallas ("3 carreras" o "Sin asignar" en `#9AA3AE`), acción Editar.
Modal "Nueva materia": Nombre; grid de 3 (Código, Créditos, Área); nota gris que remite a Malla curricular para asignar semestre; botones Cancelar / Crear materia.

### 6 · Malla curricular  ← la única pantalla admin con diseño real
**Propósito:** seleccionar una carrera y armar su malla: qué materias, en qué semestre, cuántos créditos, qué prerrequisitos.

**Cabecera** (blanca, padding 16px 28px): etiqueta "MALLA DE" + `select` de carrera (42px, 600 16px, mín. 280px); a su lado tres métricas (700 22px sobre 400 12.5px `#6B7684`): materias, créditos, semestres. Derecha: "Ver prerrequisitos" (secundario) y "Asignar materia" (primario).

**Tablero de semestres:** fila horizontal con scroll (`min-width: max-content`), `gap: 14px`, una columna de 224px por semestre (1 a 10) — es el formato mental que ya tienen todos.
- Encabezado de columna: "Semestre N" (700 15px) + créditos del semestre a la derecha (`#9AA3AE`).
- **Tarjeta de materia:** blanca, borde `#E2E5EA`, radio 9px, padding 11px 12px, `cursor: grab`; hover borde `#1D5B96` + `box-shadow: 0 3px 10px rgba(11,33,64,.08)`. Contiene nombre (600 14px/1.3), fila código monoespaciado `#9AA3AE` + créditos (500 12px `#6B7684`), y opcionalmente una línea separada por borde superior con **"Req: …"** en `#4C7CA8`, o el marcador de materia compartida (punto `#B79322` + "Compartida · 4 carreras" en `#7D6A2E`).
- Cada columna termina en un botón punteado "+ Materia" (38px, borde `#C2CAD4`, hover azul).
- **Columna destino durante arrastre:** título en `#1D5B96`, contenedor con fondo `#EAF2F9` y borde punteado `#1D5B96`, más una zona "Soltar aquí".

**Panel lateral "Asignar materia"** (`Sheet` derecho de 432px, borde izquierdo `#DDE1E7`, sombra `-18px 0 40px rgba(11,33,64,.10)`):
1. Cabecera: título + contexto "Ing. Software · semestre 6" + botón cerrar 30px.
2. **Búsqueda en el catálogo global** (input 42px enfocado).
3. Resultados:
   - **Coincidencia existente** — tarjeta con borde de 2px `#1D5B96`, fondo `#F5F9FD`, badge azul "Ya existe" y, dentro, el **aviso ámbar**: fondo `#FBF7EA`, borde `#E7DCB8`, disco `#B79322`, texto "También está en **Ing. Electrónica, semestre 5**. Úsala tal cual para que el material y el asistente se compartan entre carreras; no crees un duplicado." **Este aviso es lo que evita materias duplicadas y que se rompa el material compartido: no lo omitas.**
   - Otras coincidencias: tarjeta simple con estado a la derecha ("Ya en semestre 4", "Sin asignar").
   - Último recurso: botón punteado "Ninguna coincide · crear materia nueva".
4. Semestre en esta malla (`select`) y Créditos en esta carrera (input de 120px) — los créditos son propios de la relación carrera-materia.
5. **Prerrequisitos:** nota "Solo materias de semestres 1 a 5" (siempre semestres **anteriores** al de destino, de **esa misma carrera**). Chips navy con ✕ para los seleccionados y lista de checkboxes agrupada por semestre (encabezados `#F5F7F9`, máx. 172px con scroll).
6. Pie fijo: Cancelar / "Asignar a semestre 6".

---

## Interactions & Behavior
- **Login:** submit → autenticar → redirigir por rol (`/chat` estudiante, `/admin/carreras` coordinación).
- **Registro:** al cambiar carrera o semestre, recalcular y mostrar la lista de asistentes resultante. Validar correo institucional y coincidencia de contraseñas.
- **Chat:**
  - Cambiar de asistente en la barra lateral **inicia una conversación nueva**; nunca se arrastra contexto entre materias.
  - Enviar: `Enter` envía, `Shift+Enter` salto de línea. Entrada deshabilitada mientras hay respuesta en curso; botón de detener aborta el stream.
  - Streaming token a token; las tarjetas de herramienta aparecen en el orden en que el agente las invoca, antes del texto final.
  - Cada tarjeta de herramienta se pliega/despliega de forma independiente (`Collapsible`). Por defecto plegada salvo la primera.
  - Feedback: 👍/👎 optimista; abre el `textarea` de comentario opcional.
  - Preguntas sugeridas del estado vacío: al pulsarlas, rellenan la entrada y envían.
- **Carreras / Materias:** buscar, filtrar, crear y editar en modal. Sin borrado destructivo si la entidad está en uso en alguna malla (bloquear con mensaje).
- **Malla:** arrastrar tarjetas entre columnas cambia el semestre. Al asignar, validar que ningún prerrequisito pertenezca al mismo semestre o a uno posterior. Advertir siempre cuando la materia ya exista en otra carrera.
- **Transiciones:** hover 120–150 ms `ease-out`; spinner 0.8 s lineal; pulso del icono de herramienta 1.2 s `ease-in-out`.
- **Responsive:** el prototipo es de escritorio (1440×900). En móvil, la barra lateral del chat pasa a `Sheet`; el tablero de la malla conserva el scroll horizontal.

## State Management
**Chat (cliente):** `activeAssistant` (general | materia_id), `conversationId`, `messages[]` (rol, contenido, `toolCalls[]`, `feedback`), `runState` ∈ `idle | queued | loading_model | thinking | streaming | error`, `expandedToolCalls: Set<id>`, `abortController`.

**Servidor:** cola/semáforo de GPU (una inferencia concurrente; publicar posición en cola por SSE o WebSocket), detección de modelo no cargado para emitir `loading_model`, y timeout accionable si Ollama no responde.

**Admin:** listas paginadas de carreras y materias; para la malla, `carreraId`, `mallaEntries[]` (materia_id, semestre, créditos, prerrequisitos[]), y estado del panel de asignación (búsqueda, resultado seleccionado, semestre destino, prerrequisitos marcados).

**Modelo de datos mínimo:** `carrera`, `materia` (global), `malla` (carrera_id, materia_id, semestre, créditos) y `prerrequisito` (malla_id, materia_id_requerida); `estudiante` (carrera_id, semestre); `conversacion`, `mensaje`, `tool_call` (nombre, argumentos JSON, resultado JSON, duración_ms) y `feedback` (mensaje_id, valor, comentario).

## Design Tokens
**Color**
| Uso | Hex |
|---|---|
| Navy primario / superficies oscuras | `#0B2140` |
| Navy hover / superficie elevada | `#12345F` |
| Azul de acento (activo, enlaces) | `#1D5B96` |
| Azul claro sobre navy | `#6E9BC7` · `#C6D5E6` · `#5F82AC` |
| Fondo de app | `#F7F8FA` (marco exterior `#EDEFF2`) |
| Superficie | `#FFFFFF` |
| Borde | `#E2E5EA` · borde de control `#D3D9E0` · punteado `#C2CAD4` |
| Texto principal | `#0B2140` / cuerpo `#233240` |
| Texto secundario | `#6B7684` · terciario `#9AA3AE` · label `#3B4757` |
| Herramienta (fondo/borde/texto) | `#F3F8FC` / `#CBDCEA` / `#0F3E68` |
| Aviso ámbar | `#FBF7EA` / `#E7DCB8` / `#B79322` / `#5E4E12` |
| Error | `#FBF3F0` / `#E6C6B9` / `#A9502F` |
| Éxito (badge) | `#E7F1EA` / `#2C6544` |
| Punto de asistente activo | `#7FD1C1` |

**Tipografía:** Barlow (400/500/600/700) para toda la UI; IBM Plex Mono (400/500) para códigos, nombres de herramienta y JSON.
Escala: 46 / 32 / 30 / 26 / 22 / 19 / 17 / 15.5 / 15 / 14.5 / 14 / 13.5 / 13 / 12.5 / 12 / 11 px. Eyebrows: 11–12px, 600, uppercase, `letter-spacing: .14em`.

**Espaciado:** 4 · 8 · 12 · 16 · 20 · 22 · 26 · 28 · 44 · 64 px.
**Radio:** 6 (chip) · 7 (botón pequeño) · 8 (control) · 9–10 (tarjeta) · 12 (contenedor) · 14 (burbuja, marco) · 20px (píldora).
**Sombras:** tarjeta hover `0 3px 10px rgba(11,33,64,.08)`; barra flotante `0 6px 18px rgba(11,33,64,.08)`; modal `0 24px 60px rgba(11,33,64,.3)`; panel lateral `-18px 0 40px rgba(11,33,64,.10)`; foco `0 0 0 3px rgba(29,91,150,.14)`.
**Alturas de control:** input/botón 38–48px; fila de tabla 46px; hit target mínimo 44px.

## Assets
- `design/uploads/PacualBravoLogo.jpg` — logo institucional aportado por el usuario. **El archivo está recortado** ("PASCUAL BRAV"); sustituir por el original en SVG o PNG antes de implementar.
- Sin iconos de librería: ⚙ ✕ ↑ ■ 👍 👎 son caracteres. Al implementar, reemplazar por `lucide-react` (`Settings2`, `X`, `ArrowUp`, `Square`, `ThumbsUp`, `ThumbsDown`), salvo 👍/👎 si se prefieren los emoji.
- Fuentes desde Google Fonts: Barlow, IBM Plex Mono → usar `next/font/google`.

## Files
En `design/`, abrir cada archivo en el navegador:

| Archivo | Pantalla |
|---|---|
| `1 Login.dc.html` | Login |
| `2 Registro.dc.html` | Registro de estudiante |
| `3 Chat.dc.html` | Chat (incluye los 7 estados en un selector de demo en el encabezado) |
| `4 Carreras.dc.html` | Carreras + modal |
| `5 Materias.dc.html` | Materias + modal |
| `6 Malla.dc.html` | Malla curricular + panel de asignación |
| `support.js` | Runtime del prototipo. No se porta al proyecto. |

Notas de lectura: los estilos son inline; el estado vive en la clase `Component` al final de cada archivo. El `select` "Estado demo" del chat existe solo para inspeccionar los estados del prototipo y **no forma parte del producto**.
