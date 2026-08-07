class IdentityError(Exception):
    """Base class for identity rule violations."""


class EmailAlreadyRegistered(IdentityError):
    """An account already exists for this email address."""


class InvalidCredentials(IdentityError):
    """Email or password did not match. Never disclose which one."""
