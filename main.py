from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy import Column, JSON
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated
from collections import deque

# Global storage for webhook event logs (last 20 payloads)
webhook_logs = deque(maxlen=20)

class WebhookNote(BaseModel):
    source : str | None = Field(default=None)
    message : str = Field(..., max_length=200)
    tags : list[str] = Field(default_factory=list)

class WebhookLog(BaseModel):
    timestamp: str
    payload: WebhookNote

class Note(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True, max_length=100)
    content: str | None = Field(default=None)
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: str = Field(default_factory=lambda: datetime.now())

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# API CRUD ENDPOINTS
@app.post("/notes", response_model=Note, status_code=201)
async def create_note(note: Note):
    with Session(engine) as session:
        session.add(note)
        session.commit()
        session.refresh(note)

    return note

@app.get("/notes", response_model=list[Note])
async def read_notes(q: Annotated[str | None, Query(max_length=50)] = None, tag: Annotated[str | None, Query(max_length=20)] = None):
    with Session(engine) as session:
        note = select(Note)
        if q is not None:
            note = note.where(Note.title.contains(q.lower()) | Note.content.contains(q.lower()))
        if tag is not None:
            note = note.where(Note.tags.contains([tag]))
        notes = session.exec(note).all()
        return notes
    
@app.get("/notes/{note_id}", response_model=Note)
async def read_note(note_id: int):
    with Session(engine) as session:
        note = session.get(Note, note_id)
        if note is None:
            # return JSONResponse(status_code=404, content={"message": "404 Not Found"})
            raise HTTPException(status_code=404, detail="Not Found")
        return note
    
@app.delete("/notes/{note_id}", status_code=204)
async def delete_note(note_id: int):
    with Session(engine) as session:
        note = session.get(Note, note_id)
        if note is None:
            raise HTTPException(status_code=404, detail="404 Not Found")
        session.delete(note)
        session.commit()
    return JSONResponse(status_code=204, content=None)

@app.put("/notes/{note_id}", response_model=Note)
async def update_note(note_id: int, note: Note):
    with Session(engine) as session:
        existing_note = session.get(Note, note_id)
        if existing_note is None:
            raise HTTPException(status_code=404, detail="Not Found")
        existing_note.title = note.title
        existing_note.content = note.content
        existing_note.tags = note.tags
        session.add(existing_note)
        session.commit()
        session.refresh(existing_note)
    return existing_note

@app.get("/webhooks/logs", response_model=list[WebhookLog])
async def get_webhook_logs():
    return list(webhook_logs)

# WEBHOOK ENDPOINT
@app.post("/webhooks/note", response_model=list[Note])
async def create_note_webhook(webhook_note: WebhookNote):
    
    note = Note(
        title=webhook_note.message[:40],
        content=webhook_note.message,
        tags=webhook_note.tags + ([f"source:{webhook_note.source}"] if webhook_note.source else [])
    )
    with Session(engine) as session:
        session.add(note)
        session.commit()
        session.refresh(note)

    webhook_logs.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "payload": webhook_note.model_dump()
    })
    
    return [note]