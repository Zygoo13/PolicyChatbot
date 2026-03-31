from app.schemas import ChatResponse, SourceItem
from app.services.llm_service import generate_answer
from app.services.retrieval_service import (
    build_context_from_sources,
    is_ready,
    search_relevant_chunks,
)


RAG_SYSTEM_PROMPT = """
Bạn là trợ lý AI tư vấn policy trong quản lý dự án phần mềm.

Quy tắc bắt buộc:
- Chỉ sử dụng thông tin trong CONTEXT được cung cấp.
- Không dùng kiến thức bên ngoài CONTEXT.
- Nếu CONTEXT không đủ thì phải nói đúng câu:
  "Không đủ dữ liệu trong policy context để trả lời câu hỏi này."
- Không bịa thêm bước, vai trò, tiêu chí hoặc quy trình.
- Trả lời bằng tiếng Việt.
""".strip()


RAG_PROMPT_OUTPUT_RULES = """
Yêu cầu đầu ra:

1. Nếu câu hỏi dạng SO SÁNH (ví dụ: "khác nhau", "phân biệt"):
   → BẮT BUỘC dùng format:

Policy summary:
Key difference:
Steps:
Source note:

2. Nếu câu hỏi KHÔNG phải so sánh:
   → dùng format:

Policy summary:
Rules / Steps:
Source note:

3. Trả lời NGẮN GỌN, không lan man.
4. Không thêm thông tin ngoài CONTEXT.
5. Không dùng Markdown bảng.
""".strip()


def _build_source_note(sources: list[SourceItem]) -> str:
    if not sources:
        return "Không có nguồn phù hợp."

    primary = sources[0]
    primary_text = f"{primary.title or primary.file_name} - {primary.section or 'N/A'}"

    if len(sources) == 1:
        return f"Nguồn chính: {primary_text}"

    secondary = sources[1]
    secondary_text = (
        f"{secondary.title or secondary.file_name} - {secondary.section or 'N/A'}"
    )

    return f"""Nguồn chính: {primary_text}
Nguồn phụ: {secondary_text}"""


def handle_llm_only(question: str) -> ChatResponse:
    answer = generate_answer(user_prompt=f"Câu hỏi: {question}")

    return ChatResponse(
        mode="llm_only",
        answer=answer,
        sources=[],
    )


def handle_rag(question: str) -> ChatResponse:
    if not is_ready():
        return ChatResponse(
            mode="rag",
            answer="RAG chưa sẵn sàng: chưa có FAISS index hoặc metadata.",
            sources=[],
        )

    sources = search_relevant_chunks(question=question, top_k=2)
    context = build_context_from_sources(sources)

    if not context.strip():
        return ChatResponse(
            mode="rag",
            answer="Không tìm thấy dữ liệu policy phù hợp để trả lời câu hỏi này.",
            sources=[],
        )

    prompt = f"""
CONTEXT:
{context}

CÂU HỎI:
{question}

Hãy trả lời câu hỏi chỉ dựa trên CONTEXT ở trên.
""".strip()

    answer = generate_answer(
        user_prompt=prompt,
        system_prompt=RAG_SYSTEM_PROMPT,
    )

    return ChatResponse(
        mode="rag",
        answer=answer,
        sources=sources,
    )


def handle_rag_prompt(question: str) -> ChatResponse:
    if not is_ready():
        return ChatResponse(
            mode="rag_prompt",
            answer="RAG Prompt chưa sẵn sàng: chưa có FAISS index hoặc metadata.",
            sources=[],
        )

    sources = search_relevant_chunks(question=question, top_k=3)
    context = build_context_from_sources(sources)

    if not context.strip():
        return ChatResponse(
            mode="rag_prompt",
            answer="Không đủ dữ liệu trong policy context để trả lời câu hỏi này.",
            sources=[],
        )

    source_note = _build_source_note(sources)

    prompt = f"""
CONTEXT:
{context}

USER QUESTION:
{question}

{RAG_PROMPT_OUTPUT_RULES}

Gợi ý source note:
{source_note}
""".strip()

    answer = generate_answer(
        user_prompt=prompt,
        system_prompt=RAG_SYSTEM_PROMPT,
    )

    return ChatResponse(
        mode="rag_prompt",
        answer=answer,
        sources=sources,
    )


def answer_question(question: str, mode: str) -> ChatResponse:
    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("Question must not be empty.")

    if mode == "llm_only":
        return handle_llm_only(normalized_question)
    if mode == "rag":
        return handle_rag(normalized_question)
    if mode == "rag_prompt":
        return handle_rag_prompt(normalized_question)

    raise ValueError(f"Unsupported mode: {mode}")
