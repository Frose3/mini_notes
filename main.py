from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field as PydanticField, constr
from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy import Column, JSON
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

class Note(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    content: str = Field(default=None)
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

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


@app.post("/notes", response_model=Note, status_code=201)
async def create_note(note: Note):
    with Session(engine) as session:
        session.add(note)
        session.commit()
        session.refresh(note)

    return JSONResponse(status_code=201, content=note.model_dump())

@app.get("/notes", response_model=list[Note])
async def read_notes(q: Annotated[str | None, Query(max_length=50)] = None, tag: Annotated[str | None, Query(max_length=20)] = None):
    with Session(engine) as session:
        notes = session.exec(select(Note)).all()
        if q is not None:
            notes = [note for note in notes if q.lower() in note.title.lower() or q.lower() in note.content.lower()]
        if tag is not None:
            notes = [note for note in notes if tag in note.tags]
        return notes
    
@app.get("/notes/{note_id}", response_model=Note)
async def read_note(note_id: int):
    with Session(engine) as session:
        note = session.get(Note, note_id)
        if note is None:
            return JSONResponse(status_code=404, content={"message": "404 Not Found"})
        return note
    
@app.delete("/notes/{note_id}", status_code=204)
async def delete_note(note_id: int):
    with Session(engine) as session:
        note = session.get(Note, note_id)
        if note is None:
            return JSONResponse(status_code=404, content={"message": "404 Not Found"})
        session.delete(note)
        session.commit()
    return JSONResponse(status_code=204, content=None)

@app.put("/notes/{note_id}", response_model=Note)
async def update_note(note_id: int, note: Note):
    with Session(engine) as session:
        existing_note = session.get(Note, note_id)
        if existing_note is None:
            return JSONResponse(status_code=404, content={"message": "404 Not Found"})
        existing_note.title = note.title
        existing_note.content = note.content
        existing_note.tags = note.tags
        session.add(existing_note)
        session.commit()
        session.refresh(existing_note)
    return existing_note