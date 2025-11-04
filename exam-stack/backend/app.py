import os
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://appuser:apppass@db:5432/appdb"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
app = FastAPI(title="API Notes")

# Init table
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS notes (
            id SERIAL PRIMARY KEY,
            content TEXT NOT NULL
        )
    """))

class NoteIn(BaseModel):
    content: str

class NoteOut(BaseModel):
    id: int
    content: str

@app.get("/health")
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}

@app.get("/notes", response_model=List[NoteOut])
def list_notes():
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, content FROM notes ORDER BY id DESC")
        ).mappings().all()
    return [{"id": r["id"], "content": r["content"]} for r in rows]

@app.post("/notes", response_model=NoteOut)
def add_note(note: NoteIn):
    with engine.begin() as conn:
        row = conn.execute(
            text("INSERT INTO notes(content) VALUES (:c) RETURNING id, content"),
            {"c": note.content}
        ).mappings().first()
    return {"id": row["id"], "content": row["content"]}