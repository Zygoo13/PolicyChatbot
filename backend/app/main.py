import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import ChatRequest, ChatResponse
from app.services.chat_service import answer_question

app = FastAPI(title="Policy Chatbot API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Policy Chatbot API is running"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        return answer_question(
            question=request.question,
            mode=request.mode,
        )
    except ValueError as e:
        print("VALUE ERROR:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print("UNEXPECTED ERROR:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
