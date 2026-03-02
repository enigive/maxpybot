from typing import Optional


class MaxPyBotError(Exception):
    """Base exception for maxpybot."""


class EmptyTokenError(MaxPyBotError):
    """Raised when bot token is empty."""


class InvalidURLError(MaxPyBotError):
    """Raised when API URL cannot be parsed."""


class APIError(MaxPyBotError):
    """Represents an error response returned by MAX API."""

    def __init__(self, status_code: int, message: str, details: Optional[str] = None) -> None:
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(str(self))

    def __str__(self) -> str:
        if self.details:
            return "API error {0}: {1} ({2})".format(self.status_code, self.message, self.details)
        return "API error {0}: {1}".format(self.status_code, self.message)

    def is_attachment_not_ready(self) -> bool:
        return self.message == "attachment.not.ready"


class NetworkError(MaxPyBotError):
    """Represents a transport-level network error."""

    def __init__(self, operation: str, original_error: Exception) -> None:
        self.operation = operation
        self.original_error = original_error
        super().__init__(str(self))

    def __str__(self) -> str:
        return "Network error during {0}: {1}".format(self.operation, self.original_error)


class TimeoutError(MaxPyBotError):
    """Represents a request timeout."""

    def __init__(self, operation: str, reason: str = "") -> None:
        self.operation = operation
        self.reason = reason
        super().__init__(str(self))

    def __str__(self) -> str:
        if self.reason:
            return "Timeout error during {0}: {1}".format(self.operation, self.reason)
        return "Timeout error during {0}".format(self.operation)

    def timeout(self) -> bool:
        return True


class SerializationError(MaxPyBotError):
    """Represents JSON encode/decode failures."""

    def __init__(self, operation: str, data_type: str, original_error: Exception) -> None:
        self.operation = operation
        self.data_type = data_type
        self.original_error = original_error
        super().__init__(str(self))

    def __str__(self) -> str:
        return "Serialization error during {0} of {1}: {2}".format(
            self.operation,
            self.data_type,
            self.original_error,
        )
