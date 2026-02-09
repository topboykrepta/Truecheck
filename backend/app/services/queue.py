from __future__ import annotations

from redis import Redis
from rq import Queue

from app.config import settings
from app.services.audit import audit


def enqueue_report(report_id: str) -> bool:
    try:
        redis_conn = Redis.from_url(settings.truecheck_redis_url)
        queue = Queue(settings.truecheck_queue_name, connection=redis_conn)
        queue.enqueue("worker.worker.process_report", report_id)
        audit(report_id, "enqueue", {"queue": settings.truecheck_queue_name})
        return True
    except Exception as e:
        # If Redis/worker isn't available, fall back to in-process in API.
        audit(report_id, "enqueue_failed", {"error": str(e)})
        return False
