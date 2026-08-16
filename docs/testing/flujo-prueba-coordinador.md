# Flujo de prueba — Coordinación

Checklist manual para probar la carga de material de estudio y la administración de materias
como usuario de coordinación. Solo para ambiente local de desarrollo.

## 0. Preparar el ambiente

```bash
docker compose up -d redis
```

```bash
cd backend && ../backend/.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend && npm run dev
```

Confirmar que `ollama pull nomic-embed-text` ya corrió (requerido para que la búsqueda en
material funcione) y que el modelo de chat (`qwen2.5:3b` u otro configurado) también está
descargado.

Abrir <http://localhost:3000> e iniciar sesión con:

| Correo | Contraseña |
|---|---|
| `coordinacion@pascualbravo.edu.co` | `Coordinacion#2026` |

## 1. Descargar material de prueba

No hay materiales reales de la institución en el repo — usa estos documentos abiertos
(licencia libre) para probar la ingesta. Cada uno mapea a una materia real ya sembrada en el
programa Ingeniería de Software, semestre 5 (el mismo semestre del estudiante de prueba, para
poder probar todo con una sola cuenta):

| Materia (semestre 5) | Recurso abierto sugerido |
|---|---|
| Algebra Lineal | [Álgebra lineal (Schilling, Nachtergaele y Lankham) — LibreTexts Español](https://espanol.libretexts.org/Bookshelves/Matematicas/Algebra_lineal/Libro:_%C3%81lgebra_lineal_(Schilling,_Nachtergaele_y_Lankham)) |
| Estadistica | [Estadísticas Introductorias (OpenStax) — LibreTexts Español](https://espanol.libretexts.org/Bookshelves/Estadisticas/Estadisticas_Introductorias/Libro%3A_Estad%C3%ADsticas_Introductorias_(OpenStax)) |
| Ingles 3 | [Free English Grammar Books (PDF) — english-4u.de](https://www.english-4u.de/worksheets.htm) |

Materias de otros semestres, si quieres probar con más variedad:

| Materia | Recurso abierto sugerido |
|---|---|
| Calculo Diferencial / Calculo Integral | [Cálculo volumen 1 (OpenStax, español)](https://openstax.org/details/books/c%C3%A1lculo-volumen-1) |
| Estructura de Datos | [Estructuras de Datos — OpenLibro](https://openlibro.com/libro/estructuras-de-datos/) |
| Bases de Datos 1 / Bases de Datos II | [Bases de Datos — OpenLibro](https://openlibro.com/libro/bases-de-datos/) |

En LibreTexts Español, cada capítulo tiene un botón para exportar/guardar como PDF; en
OpenStax hay un botón "Download a PDF" en la página de detalle del libro. Basta con 5-15
páginas de cualquiera de estos libros para probar la ingesta — no hace falta el libro completo.

## 2. Subir material a una materia

- [ ] Ir a **Materias**, abrir la materia **Algebra Lineal** (o la que elijas), abrir el modal
      de edición.
- [ ] En la sección **Material de estudio**, subir el PDF descargado.
- [ ] Confirmar que aparece en la lista con su nombre de archivo apenas termina de subir (sin
      recargar la página).
- [ ] Cerrar y volver a abrir el modal — el material debe seguir listado (persistencia real,
      no solo estado local).

## 3. Casos de error

- [ ] Subir un archivo con extensión no soportada (ej. un `.txt` o `.pptx` cualquiera). Debe
      mostrarse un mensaje de error legible en el modal (no un error genérico ni una pantalla
      en blanco), y la lista de materiales existentes no debe desaparecer ni corromperse.
- [ ] Con el backend de Ollama detenido (`Ctrl+C` en la terminal de `ollama serve`, si corre
      aparte, o deteniendo el servicio), intentar subir un PDF válido — debe fallar con un
      mensaje de error visible, y la materia **no** debe quedar listada como si el material se
      hubiera subido correctamente (si queda un material sin contenido buscable, es un bug:
      reportarlo).
- [ ] Eliminar un material de la lista — debe desaparecer inmediatamente y no debe poder
      buscarse desde el chat de un estudiante después de eliminado.

## 4. Verificar aislamiento de acceso

- [ ] Cerrar sesión y volver a entrar como el estudiante de prueba
      (`jose.hernandez540@pascualbravo.edu.co` / `Estudiante#2026`). Confirmar que **no** hay
      ninguna opción de subir/eliminar material visible en ninguna pantalla del estudiante —
      esa función es exclusiva de coordinación.
- [ ] (Opcional, vía `curl` o Postman) Llamar `POST /api/v1/admin/courses/{id}/materials` con
      el token del estudiante en vez del de coordinación — debe responder `401`.

## 5. Siguiente paso

Con material subido a **Algebra Lineal**, **Estadistica** e **Ingles 3**, seguir con
`flujo-prueba-estudiante.md` usando la misma cuenta de estudiante — está en el semestre 5,
así que las tres materias con material ya están disponibles como asistentes por materia.
