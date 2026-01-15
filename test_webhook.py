
import hmac, hashlib, json
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def sign(body: bytes):
    return hmac.new(settings.WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

def test_webhook_insert_and_duplicate():
    body = {
        "message_id": "m1",
        "from": "+919876543210",
        "to": "+14155550100",
        "ts": "2025-01-15T10:00:00Z",
        "text": "Hello"
    }
    raw = json.dumps(body).encode()
    sig = sign(raw)

    r1 = client.post("/webhook", data=raw, headers={"X-Signature": sig})
    assert r1.status_code == 200

    r2 = client.post("/webhook", data=raw, headers={"X-Signature": sig})
    assert r2.status_code == 200
