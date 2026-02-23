"""LiveDocAI API – Phase 1."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, documents, health, history, profile

app = FastAPI(
    title="LiveDocAI",
    description="Smart Document Q&A – upload docs, ask questions, get cited answers.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://intelligent-doc-search.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(profile.router)
app.include_router(history.router)


@app.get("/")
def root():
    return {"app": "LiveDocAI", "docs": "/docs"}
