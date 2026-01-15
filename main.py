
import hmac, hashlib, sqlite3
from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel, constr
from datetime import datetime
from app.config import settings
from app.models import init_db
from app.storage import MessageStore
from app.logging_utils import RequestLogger
from app.metrics import http_requests, webhook_requests, latency
from prometheus_client import generate_latest

app = FastAPI()
app.middleware("http")(RequestLogger())

if not settings.WEBHOOK_SECRET:
    raise RuntimeError("WEBHOOK_SECRET not set")

db_path = settings.DATABASE_URL.replace("sqlite:///", "")
conn = init_db(db_path)
store = MessageStore(conn)

class WebhookMsg(BaseModel):
    message_id: constr(min_length=1)
    from_: constr(regex=r"^\+\d+$", alias="from")
    to: constr(regex=r"^\+\d+$")
    ts: constr(regex=r"Z$")
    text: constr(max_length=4096) | None = None

@app.post("/webhook")
async def webhook(request: Request, x_signature: str = Header(None)):
    body = await request.body()
    request.state.webhook_log = {"dup": False}

    if not x_signature:
        webhook_requests.labels("invalid_signature").inc()
        request.state.webhook_log["result"] = "invalid_signature"
        raise HTTPException(401, "invalid signature")

    sig = hmac.new(
        settings.WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(sig, x_signature):
        webhook_requests.labels("invalid_signature").inc()
        request.state.webhook_log["result"] = "invalid_signature"
        raise HTTPException(401, "invalid signature")

    try:
        msg = WebhookMsg.parse_raw(body)
    except Exception:
        webhook_requests.labels("validation_error").inc()
        request.state.webhook_log["result"] = "validation_error"
        raise

    payload = msg.dict(by_alias=True)
    payload["created_at"] = datetime.utcnow().isoformat() + "Z"

    created = store.insert_message(payload)
    request.state.webhook_log["message_id"] = payload["message_id"]

    if created:
        webhook_requests.labels("created").inc()
        request.state.webhook_log["result"] = "created"
    else:
        webhook_requests.labels("duplicate").inc()
        request.state.webhook_log["result"] = "duplicate"
        request.state.webhook_log["dup"] = True

    return {"status": "ok"}

@app.get("/messages")
async def messages(limit: int = 50, offset: int = 0, from_: str = None, since: str = None, q: str = None):
    data, total = store.list_messages(limit, offset, from_, since, q)
    http_requests.labels("/messages", "200").inc()
    return {"data": data, "total": total, "limit": limit, "offset": offset}

@app.get("/stats")
async def stats():
    http_requests.labels("/stats", "200").inc()
    return store.stats()

@app.get("/health/live")
async def live():
    return {"status": "live"}

@app.get("/health/ready")
async def ready():
    try:
        conn.execute("SELECT 1")
        if not settings.WEBHOOK_SECRET:
            raise Exception("secret missing")
    except Exception:
        raise HTTPException(503, "not ready")
    return {"status": "ready"}

@app.get("/metrics")
async def metrics():
    return generate_latest()
