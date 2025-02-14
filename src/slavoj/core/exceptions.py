class BaseError(Exception):
    """Base error class for the application."""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ConfigurationError(BaseError):
    """Raised when there are configuration-related errors."""

    pass


class DatabaseError(BaseError):
    """Raised when database operations fail."""

    pass


class MessageDeliveryError(BaseError):
    """Raised when message delivery fails."""

    pass


class LLMError(BaseError):
    """Raised when LLM operations fail."""

    pass


class BookProcessingError(BaseError):
    """Raised when book processing fails."""

    pass


class ResponseAggregationError(BaseError):
    """Raised when response aggregation fails."""

    pass


class ConversationError(BaseError):
    """Raised when conversation processing fails."""

    pass


class AuthenticationError(BaseError):
    """Raised when authentication fails."""

    pass
