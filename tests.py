import pytest
from main import app, webhook_logs
from fastapi.testclient import TestClient

def test_create_note():

    with TestClient(app) as client: # Required "with" because of lifespan events that create the database tables

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

def test_get_notes():

    with TestClient(app) as client:

        response = client.get("/notes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        response = client.get("/notes?q=test note")
        assert response.status_code == 200

        response = client.get("/notes?tag=note")
        assert response.status_code == 200

def test_webhook_note_creation():

    with TestClient(app) as client:

        response = client.post("/webhooks/note", json={
            "source": "test_source",
            "message": "This is a webhook test note.",
            "tags": ["webhook", "test"]
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "This is a webhook test note."
        assert data[0]["content"] == "This is a webhook test note."
        assert "source:test_source" in data[0]["tags"]

def test_webhook_logs():

    with TestClient(app) as client:
    
        webhook_logs.clear()

        client.post("/webhooks/note", json={
            "source": "test_source",
            "message": "Log this event.",
            "tags": ["log"]
        })

        response = client.get("/webhooks/logs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "timestamp" in data[0]
        assert "payload" in data[0]
        assert data[0]["payload"]["message"] == "Log this event."