class AppError(Exception):
    """Application failure, independent of Telegram and user-facing wording."""


class EmptyRequestError(AppError):
    pass


class ModelTimeoutError(AppError):
    pass


class ModelRateLimitError(AppError):
    pass


class ModelUnavailableError(AppError):
    pass


class InvalidModelResponseError(AppError):
    pass


class TranscriptionError(AppError):
    pass


class VoiceLimitError(AppError):
    pass
