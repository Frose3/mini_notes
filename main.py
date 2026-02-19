from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy import Column, JSON
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated
from collections import deque
import os

WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN", default="your-secret-token")

# Global storage for webhook event logs (last 20 payloads)
webhook_logs = deque(maxlen=20)

class WebhookNote(BaseModel):
    source : str | None = Field(default=None)
    message : str = Field(..., max_length=200)
    tags : list[str] = Field(default_factory=list)

class WebhookLog(BaseModel):
    timestamp: str
    payload: WebhookNote

class NoteRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str | None = Field(default=None)
    tags: list[str] = Field(default_factory=list)

class Note(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True, min_length=1, max_length=100)
    content: str | None = Field(default=None)
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Lifespan event to create database tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# API CRUD ENDPOINTS
@app.post("/notes", response_model=Note, status_code=201)
async def create_note(note: NoteRequest):
    note = Note(**note.model_dump())

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

@app.put("/notes/{note_id}", response_model=Note)
async def update_note(note_id: int, note: NoteRequest):
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

# WEBHOOK ENDPOINT
@app.post("/webhooks/note", response_model=list[Note])
async def create_note_webhook(webhook_note: WebhookNote, X_Webhook_Token: Annotated[str | None, Header()] = None):
    
    if X_Webhook_Token != WEBHOOK_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

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
        "timestamp": datetime.now().isoformat(),
        "payload": webhook_note.model_dump()
    })
    
    return [note]

@app.get("/webhooks/logs", response_model=list[WebhookLog])
async def get_webhook_logs():
    return list(webhook_logs)