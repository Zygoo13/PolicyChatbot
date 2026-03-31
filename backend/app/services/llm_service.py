from typing import Optional

import google.generativeai as genai

from app.core.config import settings
from app.core.exceptions import AIServiceError, ConfigurationError


DEFAULT_SYSTEM_PROMPT = """
Bạn là trợ lý AI hỗ trợ tư vấn policy trong quản lý dự án phần mềm.

Nguyên tắc:
- Trả lời rõ ràng, chính xác, dễ hiểu.
- Nếu được cung cấp context thì ưu tiên bám sát context.
- Không bịa thêm thông tin không có căn cứ.
- Trả lời bằng tiếng Việt.
""".strip()


_model = None


def _get_model():
    global _model

    if not settings.GEMINI_API_KEY.strip():
        raise ConfigurationError("Thiếu GEMINI_API_KEY trong file .env")

    if _model is None:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _model = genai.GenerativeModel(settings.GEMINI_MODEL)

    return _model


def generate_answer(user_prompt: str, system_prompt: Optional[str] = None) -> str:
    prompt = f"{system_prompt or DEFAULT_SYSTEM_PROMPT}\n\n{user_prompt}".strip()

    try:
        model = _get_model()
        response = model.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        raise AIServiceError("Mô hình không trả về nội dung hợp lệ.")
    except (ConfigurationError, AIServiceError):
        raise
    except Exception as exc:
        raise AIServiceError(f"Lỗi khi gọi Gemini API: {exc}") from exc
