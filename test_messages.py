
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_messages_list():
    r = client.get("/messages")
    assert r.status_code == 200
    assert "data" in r.json()
    assert "total" in r.json()
