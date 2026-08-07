# Module: identity

Owns users, roles and student profiles.

## Domain
- `Role` — `coordination` or `student`. There is no teacher role in Phase 1.
- `User(email, password_hash, role)`.
- `StudentProfile(user_id, first_name, last_name, document, program_id, current_semester)` —
  `program_id` and `current_semester` are the context that drives assistant selection, not
  ordinary profile fields.

## Key rules
- Students self-register. Coordination accounts are created by `app.cli.seed`; Phase 1 has
  no user-management screen by design.
- `InvalidCredentialsError` is raised identically for an unknown email and a wrong password, so
  the API cannot be used to enumerate accounts.
- Passwords are hashed with Argon2. Access tokens are JWTs carrying `sub` and `role`.

## Boundary
`require_authentication` in `app/api/v1/deps.py` is the only place identity enters the
system. Agent tools take `user_id` from there and never from a model-supplied argument.
