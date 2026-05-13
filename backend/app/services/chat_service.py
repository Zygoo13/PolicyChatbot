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


KNOWN_SECTIONS = [
    "Sprint Planning",
    "Daily Standup",
    "Sprint Review",
    "Sprint Retrospective",
    "Product Backlog Management",
    "User Story Estimation",
    "Definition of Done",
    "Sprint Backlog Update",
    "Agile Communication",
    "Agile Documentation",
    "Change Request Submission",
    "Change Impact Analysis",
    "Change Approval",
    "Emergency Change",
    "Change Testing",
    "Change Deployment",
    "Change Rollback",
    "Change Documentation",
    "Change Review",
    "Change Communication",
    "Code Review",
    "Unit Testing",
    "Integration Testing",
    "Regression Testing",
    "Bug Tracking",
    "QA Release Approval",
    "Performance Testing",
    "Security Testing",
    "Test Documentation",
    "Quality Metrics",
    "Incident Reporting",
    "Incident Classification",
    "Incident Response",
    "Incident Escalation",
    "Incident Resolution",
    "Incident Communication",
    "Incident Monitoring",
    "Incident Postmortem",
    "Incident Knowledge Base",
    "Incident Prevention",
]


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


def _normalize_question(question: str) -> str:
    return " ".join(question.strip().split())


def _rewrite_question_for_retrieval(question: str) -> list[str]:
    """
    Sinh ra một vài biến thể query retrieval để tăng khả năng lấy đúng source.
    Không sửa nghĩa câu hỏi gốc, chỉ hỗ trợ truy xuất.
    """
    normalized = _normalize_question(question)
    lower_q = normalized.lower()

    candidates: list[str] = [normalized]

    for section_name in KNOWN_SECTIONS:
        if section_name.lower() in lower_q:
            candidates.append(section_name)
            break

    if "vai trò" in lower_q and "phạm vi" in lower_q:
        candidates.append(
            normalized.replace("và policy này áp dụng cho phạm vi nào", "").strip()
        )
    elif "vai trò" in lower_q:
        candidates.append(
            " ".join(
                [
                    word
                    for word in normalized.split()
                    if word.lower() not in {"những", "nào", "liên", "quan", "đến"}
                ]
            ).strip()
        )
    elif "bước" in lower_q or "quy trình" in lower_q:
        candidates.append(
            normalized.replace("gồm những bước nào", "")
            .replace("quy trình", "")
            .strip()
        )

    deduped: list[str] = []
    seen = set()

    for item in candidates:
        cleaned = _normalize_question(item)
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        deduped.append(cleaned)

    return deduped


def _retrieve_with_fallback(question: str, top_k: int) -> list[SourceItem]:
    """
    Thử retrieval nhiều lần với các query biến thể.
    Gộp kết quả, loại trùng và trả về tối đa top_k nguồn.
    """
    candidate_queries = _rewrite_question_for_retrieval(question)

    merged_sources: list[SourceItem] = []
    seen_keys = set()

    for query in candidate_queries:
        sources = search_relevant_chunks(question=query, top_k=top_k)

        for src in sources:
            key = src.chunk_id or f"{src.file_name}::{src.section}::{src.title}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            merged_sources.append(src)

        if len(merged_sources) >= top_k:
            break

    return merged_sources[:top_k]


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

    sources = _retrieve_with_fallback(question=question, top_k=2)
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

    sources = _retrieve_with_fallback(question=question, top_k=3)
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
    normalized_question = _normalize_question(question)
    if not normalized_question:
        raise ValueError("Question must not be empty.")

    if mode == "llm_only":
        return handle_llm_only(normalized_question)
    if mode == "rag":
        return handle_rag(normalized_question)
    if mode == "rag_prompt":
        return handle_rag_prompt(normalized_question)

    raise ValueError(f"Unsupported mode: {mode}")
