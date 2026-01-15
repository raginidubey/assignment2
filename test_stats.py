
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_stats():
    r = client.get("/stats")
    assert r.status_code == 200
    assert "total_messages" in r.json()
