---
description: Verify backend layer boundaries and run the full test suite
---

Run these from the repository root and report the results:

1. `backend/.venv/Scripts/python.exe -m pytest backend/tests/architecture -v`
2. `backend/.venv/Scripts/python.exe -m pytest backend/tests -v`
3. `backend/.venv/Scripts/python.exe -m ruff check backend/app backend/tests`
4. `backend/.venv/Scripts/python.exe -m mypy backend/app`

If step 1 fails, name the offending file and the forbidden import, and explain which layer
rule it breaks. Do not fix by adding the package to `FORBIDDEN_ROOTS` exceptions — move
the dependency out of `app/domain/` instead.
