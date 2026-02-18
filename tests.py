import pytest
from main import app
from fastapi.testclient import TestClient

def test_create_note():

    client = TestClient(app)

    response = client.post("/notes", json={
        "title": "Test Note",
        "content": "This is a test note.",
        "tags": ["test", "note"]
    })

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Note"
    assert data["content"] == "This is a test note."
    assert data["tags"] == ["test", "note"]