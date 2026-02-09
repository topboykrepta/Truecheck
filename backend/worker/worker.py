from __future__ import annotations

import os

from redis import Redis
from rq import Worker, Queue, Connection

from app.config import settings
from app.services.pipeline import run_pipeline


def process_report(report_id: str) -> None:
    run_pipeline(report_id)


def main() -> None:
    redis_conn = Redis.from_url(settings.truecheck_redis_url)
    with Connection(redis_conn):
        worker = Worker([Queue(settings.truecheck_queue_name)])
        worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
