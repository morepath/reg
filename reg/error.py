class RegistrationError(Exception):
    """Registration error.
    """


class KeyExtractorError(Exception):
    """A lookup key could not be constructed.
    """


class NoImplicitLookupError(Exception):
    """No implicit lookup was registered.

    Register an implicit lookup by calling
    `reg.implicit.initialize()`, or pass an explicit ``lookup``
    argument to generic function calls.
    """
