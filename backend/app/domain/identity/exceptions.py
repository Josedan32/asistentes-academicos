class IdentityError(Exception):
    pass


class EmailAlreadyRegisteredError(IdentityError):
    pass


class InvalidCredentialsError(IdentityError):
    pass
