class AppError(Exception):
    """Base exception cho ứng dụng."""


class ConfigurationError(AppError):
    """Lỗi cấu hình, ví dụ thiếu API key."""


class AIServiceError(AppError):
    """Lỗi khi gọi provider AI."""
