"""Toyota Connected Services API exceptions."""


class ToyotaLoginError(Exception):
    """Raise if a login error happens."""


class ToyotaLoginServerError(ToyotaLoginError):
    """Raise if Toyota's login service fails with a server-side error.

    Raised for HTTP 5xx and 429 answers during authentication, authorization,
    token retrieval or token refresh. The credentials were not rejected, so
    callers can treat this as transient and retry later. It subclasses
    ToyotaLoginError so existing ``except ToyotaLoginError`` handlers still
    catch it.
    """

    def __init__(self, message: str, status_code: int) -> None:
        """Store the HTTP status code that Toyota answered with."""
        super().__init__(message)
        self.status_code = status_code


class ToyotaInvalidUsernameError(Exception):
    """Raise if username is invalid."""


class ToyotaRegionNotSupportedError(Exception):
    """Raise if region is not supported."""


class ToyotaApiError(Exception):
    """Raise if a API error occurres."""


class ToyotaInternalError(Exception):
    """Raise if an internal server error occurres from Toyota."""


class ToyotaActionNotSupportedError(ToyotaApiError):
    """Raise if an action is not supported on a vehicle."""
