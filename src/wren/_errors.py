from __future__ import annotations


class WrenError(Exception):
    def __init__(self, status: int, body: object, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.body = body


class WrenNotFoundError(WrenError):
    def __init__(self, body: object) -> None:
        super().__init__(404, body, "Not found")


class WrenUnauthorizedError(WrenError):
    def __init__(self, body: object) -> None:
        super().__init__(401, body, "Unauthorized")


class WrenForbiddenError(WrenError):
    def __init__(self, body: object) -> None:
        super().__init__(403, body, "Forbidden")


class WrenValidationError(WrenError):
    def __init__(self, body: object, details: list[str]) -> None:
        super().__init__(422, body, f"Validation error: {', '.join(details)}")
        self.details = details


class WrenVersionMismatchError(WrenError):
    """A conditional write (``if_version``) failed: the document is at another
    version now (``current_version``; 0 when it doesn't exist)."""

    def __init__(self, body: object) -> None:
        super().__init__(412, body, "Version mismatch")
        current = body.get("currentVersion") if isinstance(body, dict) else None
        self.current_version: int = current if isinstance(current, int) else 0
