from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_docs_available():
    assert client.get("/docs").status_code == 200
