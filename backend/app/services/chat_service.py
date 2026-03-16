from app.schemas import ChatResponse
from app.services.llm_service import generate_answer
from app.services.retrieval_service import (
    search_relevant_chunks,
    build_context_from_sources,
    is_ready,
)


RAG_PROMPT_TEMPLATE = """
Bạn là trợ lý AI tư vấn policy trong quản lý dự án phần mềm.

Nhiệm vụ:
- Trả lời câu hỏi của người dùng CHỈ dựa trên phần CONTEXT được cung cấp.
- Không sử dụng kiến thức bên ngoài CONTEXT.
- Nếu CONTEXT không đủ thông tin để trả lời chính xác, phải nói rõ: "Không đủ dữ liệu trong policy context để trả lời câu hỏi này."

Yêu cầu đầu ra:
1. Trả lời bằng tiếng Việt, rõ ràng, ngắn gọn, dễ hiểu.
2. Cấu trúc câu trả lời theo đúng 3 phần:
   - Policy summary
   - Rules / Steps
   - Source note
3. Trong phần Source note, nêu ngắn gọn tên file hoặc chunk liên quan nếu có.
4. Không bịa thêm quy trình, vai trò, hoặc yêu cầu không xuất hiện trong CONTEXT.
5. Nếu câu hỏi là định nghĩa, trả lời đúng trọng tâm định nghĩa trước.
""".strip()


def handle_llm_only(question: str) -> ChatResponse:
    answer = generate_answer(user_prompt=question)

    return ChatResponse(
        mode="llm_only",
        answer=answer,
        sources=[],
    )


def handle_rag(question: str) -> ChatResponse:
    if not is_ready():
        return ChatResponse(
            mode="rag",
            answer="RAG chưa sẵn sàng: chưa có FAISS index hoặc retrieval service chưa được cấu hình.",
            sources=[],
        )

    sources = search_relevant_chunks(question=question, top_k=3)
    context = build_context_from_sources(sources)

    if not context.strip():
        return ChatResponse(
            mode="rag",
            answer="Không tìm thấy dữ liệu policy phù hợp để trả lời câu hỏi này.",
            sources=[],
        )

    prompt = f"""
Hãy trả lời câu hỏi của người dùng dựa trên context sau.

CONTEXT:
{context}

QUESTION:
{question}
""".strip()

    answer = generate_answer(user_prompt=prompt)

    return ChatResponse(
        mode="rag",
        answer=answer,
        sources=sources,
    )


def handle_rag_prompt(question: str) -> ChatResponse:
    if not is_ready():
        return ChatResponse(
            mode="rag_prompt",
            answer="RAG Prompt chưa sẵn sàng: chưa có FAISS index hoặc retrieval service chưa được cấu hình.",
            sources=[],
        )

    sources = search_relevant_chunks(question=question, top_k=3)
    context = build_context_from_sources(sources)
    source_names = list({s.file_name for s in sources})
    source_text = ", ".join(source_names)

    if not context.strip():
        return ChatResponse(
            mode="rag_prompt",
            answer="Không đủ dữ liệu trong policy context để trả lời câu hỏi này.",
            sources=[],
        )

    prompt = f"""
CONTEXT:
{context}

USER QUESTION:
{question}

Khi trả lời hãy trích dẫn nguồn dưới dạng:
Khi trả lời hãy trích dẫn nguồn dưới dạng:
""".strip()

    answer = generate_answer(
        user_prompt=prompt,
        system_prompt=RAG_PROMPT_TEMPLATE,
    )

    return ChatResponse(
        mode="rag_prompt",
        answer=answer,
        sources=sources,
    )


def answer_question(question: str, mode: str) -> ChatResponse:
    question = question.strip()
    if not question:
        raise ValueError("Question must not be empty.")

    if mode == "llm_only":
        return handle_llm_only(question)
    elif mode == "rag":
        return handle_rag(question)
    elif mode == "rag_prompt":
        return handle_rag_prompt(question)
    else:
        raise ValueError(f"Unsupported mode: {mode}")
