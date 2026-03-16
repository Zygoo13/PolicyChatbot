# # Sẽ dùng ở bước kết nối OpenAI API
# from openai import OpenAI

# from app.core.config import settings


# client = OpenAI(api_key=settings.openai_api_key)


# SYSTEM_PROMPT = """
# Bạn là trợ lý AI hỗ trợ tư vấn policy trong quản lý dự án phần mềm.
# Hãy trả lời ngắn gọn, rõ ràng, dễ hiểu cho sinh viên.
# Nếu câu hỏi mơ hồ, hãy nêu giả định của bạn trước khi trả lời.
# """


# def get_chatgpt_answer(question: str) -> str:
#     response = client.responses.create(
#         model="gpt-5.4",
#         instructions=SYSTEM_PROMPT,
#         input=question,
#     )
#     return response.output_text


import google.generativeai as genai

from app.core.config import settings
from app.core.exceptions import ConfigurationError, AIServiceError


SYSTEM_PROMPT = """
Bạn là trợ lý AI hỗ trợ tư vấn policy trong quản lý dự án phần mềm.
Hãy trả lời ngắn gọn, rõ ràng, dễ hiểu cho sinh viên.
Nếu câu hỏi không rõ ngữ cảnh, hãy nêu giả định ngắn gọn trước khi trả lời.
Không sử dụng Markdown.
Không dùng ký hiệu như **, *, #, -, ``` trong câu trả lời.
Chỉ trả về văn bản thuần (plain text).
"""


def get_chatgpt_answer(question: str) -> str:
    api_key = settings.openai_api_key.strip()

    if not api_key:
        raise ConfigurationError("Thiếu API key trong file .env")

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        # gemini-2.5-flash

        prompt = f"{SYSTEM_PROMPT}\n\nCâu hỏi của người dùng: {question}"
        response = model.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        raise AIServiceError("Model không trả về nội dung.")
    except ConfigurationError:
        raise
    except Exception as e:
        raise AIServiceError(f"Lỗi khi gọi Gemini API: {str(e)}") from e
