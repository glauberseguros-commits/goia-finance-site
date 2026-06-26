class GOIAException(Exception):
    """Exceção base da plataforma."""


class ValidationError(GOIAException):
    pass


class AuthenticationError(GOIAException):
    pass


class RepositoryError(GOIAException):
    pass


class IntegrationError(GOIAException):
    pass
