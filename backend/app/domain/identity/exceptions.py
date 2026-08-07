class IdentityError(Exception):
    """Base class for identity rule violations."""


class EmailAlreadyRegisteredError(IdentityError):
    """An account already exists for this email address."""


class InvalidCredentialsError(IdentityError):
    """Email or password did not match. Never disclose which one."""
