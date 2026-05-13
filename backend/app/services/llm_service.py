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

    api_key = settings.GEMINI_API_KEY.strip()
    model_name = settings.GEMINI_MODEL.strip()

    if not api_key:
        raise ConfigurationError("Thiếu GEMINI_API_KEY trong file .env")

    if not model_name:
        raise ConfigurationError("Thiếu GEMINI_MODEL trong file .env")

    if _model is None:
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel(model_name)

    return _model


def generate_answer(user_prompt: str, system_prompt: Optional[str] = None) -> str:
    normalized_user_prompt = user_prompt.strip()
    if not normalized_user_prompt:
        raise AIServiceError("user_prompt không được để trống.")

    final_system_prompt = (system_prompt or DEFAULT_SYSTEM_PROMPT).strip()
    prompt = f"{final_system_prompt}\n\n{normalized_user_prompt}".strip()

    try:
        model = _get_model()
        response = model.generate_content(prompt)

        text = getattr(response, "text", None)
        if text and text.strip():
            return text.strip()

        raise AIServiceError("Mô hình không trả về nội dung hợp lệ.")
    except (ConfigurationError, AIServiceError):
        raise
    except Exception as exc:
        raise AIServiceError(f"Lỗi khi gọi Gemini API: {exc}") from exc
