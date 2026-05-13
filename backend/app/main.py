import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.exceptions import AIServiceError, ConfigurationError
from app.schemas import ChatRequest, ChatResponse
from app.services.chat_service import answer_question
from app.services.retrieval_service import is_ready


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Policy Chatbot API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Policy Chatbot API is running",
        "rag_ready": is_ready(),
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "rag_ready": is_ready(),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        return answer_question(
            question=request.question,
            mode=request.mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ConfigurationError as exc:
        logger.exception("Configuration error while processing /chat")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except AIServiceError as exc:
        logger.exception("AI service error while processing /chat")
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected server error while processing /chat")
        raise HTTPException(
            status_code=500,
            detail="Unexpected server error.",
        ) from exc
