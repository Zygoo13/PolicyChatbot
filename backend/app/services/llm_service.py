import google.generativeai as genai
from app.core.config import settings


DEFAULT_SYSTEM_PROMPT = """
Bạn là trợ lý AI hỗ trợ tư vấn policy trong quản lý dự án phần mềm.
Hãy trả lời rõ ràng, dễ hiểu.
""".strip()


def _build_model():
    if not settings.GEMINI_API_KEY:
        raise ValueError("Thiếu GEMINI_API_KEY trong file .env")

    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)


def generate_answer(user_prompt: str, system_prompt: str = None) -> str:
    system_text = system_prompt or DEFAULT_SYSTEM_PROMPT
    full_prompt = f"{system_text}\n\nUser question:\n{user_prompt}"

    model = _build_model()
    response = model.generate_content(full_prompt)

    if hasattr(response, "text") and response.text:
        return response.text.strip()

    return "Xin lỗi, mô hình chưa trả về nội dung hợp lệ."
