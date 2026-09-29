import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.rag_service import RAGService

app = FastAPI(
    title="Groq + ChromaDB RAG API",
    version="1.0.0",
)

# Current file ki Directory Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Static files (style.css aur script.js) serve karne ke liye mounting
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")

rag_service: Optional[RAGService] = None


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
    )
    source: Optional[str] = None


@app.on_event("startup")
def startup() -> None:
    global rag_service
    print("Starting RAG service...")
    try:
        rag_service = RAGService()
        print("RAG service started successfully.")
    except Exception as exc:
        print(f"RAG startup failed: {exc}")
        raise


# Browser mein Main URL (http://127.0.0.1:8000/) kholne ke liye
@app.get("/", response_class=HTMLResponse)
def read_index():
    index_path = os.path.join(BASE_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="index.html file nahi mili!")
    return FileResponse(index_path)


@app.get("/health")
def health():
    if rag_service is None:
        return {"status": "starting"}

    return {
        "status": "ok",
        "indexed_chunks": rag_service.store.count(),
    }


@app.post("/rag/query")
def query_rag(payload: QuestionRequest):
    if rag_service is None:
        raise HTTPException(
            status_code=503,
            detail="RAG service is not ready.",
        )

    try:
        return rag_service.ask(
            question=payload.question,
            top_k=payload.top_k,
            source=payload.source,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc