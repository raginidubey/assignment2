
import json, logging, time, uuid
from datetime import datetime

logger = logging.getLogger("api")
logging.basicConfig(level=logging.INFO)

class RequestLogger:
    async def __call__(self, request, call_next):
        start = time.time()
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        latency = int((time.time() - start) * 1000)

        log = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": "INFO",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "latency_ms": latency,
        }

        if hasattr(request.state, "webhook_log"):
            log.update(request.state.webhook_log)

        logger.info(json.dumps(log))
        return response
