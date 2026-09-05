# python3 -m uvicorn app.main:app --port 8000

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from pinecone import Pinecone

BASE_DIR = Path(__file__).resolve().parent

load_dotenv()

app = FastAPI(title="Swami Podcasts Chat")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _allowed_origins() -> list[str]:
    """Read the browser origins permitted to call this API."""
    configured_origins = os.environ.get(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000",
    )
    return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
ASSISTANT_NAME = os.environ.get("PINECONE_ASSISTANT_NAME", "swami-podcasts")
PINECONE_MODEL = os.environ.get("PINECONE_MODEL", "gpt-4o-mini")

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    collection: Literal["all", "BhagavadGita", "Upanishad"] = "all"


class Citation(BaseModel):
    file_name: str
    collection: str | None = None
    highlight: str | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]


def _collection_filter(collection: str) -> dict | None:
    if collection == "all":
        return None
    return {"collection": {"$eq": collection}}


def _citation_file_metadata(reference) -> dict:
    file_obj = getattr(reference, "file", None)
    if file_obj is None:
        return {}
    return getattr(file_obj, "metadata", None) or {}


def _citation_file_name(reference) -> str:
    file_obj = getattr(reference, "file", None)
    if file_obj is None:
        return "Unknown source"
    metadata = getattr(file_obj, "metadata", None) or {}
    return metadata.get("file_name") or getattr(file_obj, "name", "Unknown source")


def _format_citations(raw_citations) -> list[Citation]:
    citations: list[Citation] = []
    seen: set[tuple[str, str | None, str | None]] = set()

    for raw_citation in raw_citations or []:
        for reference in getattr(raw_citation, "references", []) or []:
            metadata = _citation_file_metadata(reference)
            highlight_obj = getattr(reference, "highlight", None)
            highlight = getattr(highlight_obj, "content", None) if highlight_obj else None
            citation = Citation(
                file_name=_citation_file_name(reference),
                collection=metadata.get("collection"),
                highlight=highlight,
            )
            key = (citation.file_name, citation.collection, citation.highlight)
            if key not in seen:
                citations.append(citation)
                seen.add(key)

    return citations


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
    )


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "assistant_name": ASSISTANT_NAME,
        "model": PINECONE_MODEL,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    prompt = (
        "Answer using only the uploaded podcast transcripts. "
        "If the user asks for a quote, provide an exact excerpt from the transcripts "
        "and briefly explain why it answers the question. "
        "If the transcripts do not support an answer, say that you could not find it.\n\n"
        f"User question: {request.question}"
    )

    try:
        response = pc.assistants.chat(
            assistant_name=ASSISTANT_NAME,
            messages=[{"role": "user", "content": prompt}],
            model=PINECONE_MODEL,
            temperature=0.2,
            filter=_collection_filter(request.collection),
            include_highlights=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ChatResponse(
        answer=response.message.content,
        citations=_format_citations(response.citations),
    )