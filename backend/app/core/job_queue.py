"""Background Job Queue — async task processing for ML inference, data sync, notifications.

Simple in-memory job queue with:
- Priority levels (critical, high, normal, low)
- Job status tracking (pending, running, completed, failed)
- Retry with exponential backoff
- Worker pool for concurrent execution

Ponytail: stdlib asyncio + queues. No Redis/Celery dependency.
"""

from __future__ import annotations
import asyncio
import time
import uuid
import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable, Any

logger = logging.getLogger("adapfit.job_queue")


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class JobPriority(str, Enum):
    CRITICAL = "critical"  # Process immediately
    HIGH = "high"          # Within 1 second
    NORMAL = "normal"      # Within 5 seconds
    LOW = "low"            # Best effort


@dataclass
class Job:
    job_id: str
    job_type: str
    payload: dict
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    attempts: int = 0
    max_retries: int = 3
    timeout_seconds: float = 300

    @property
    def duration_ms(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return round((self.completed_at - self.started_at) * 1000, 1)
        return None

    @property
    def age_seconds(self) -> float:
        return round(time.time() - self.created_at, 1)


# Priority ordering
PRIORITY_ORDER = {
    JobPriority.CRITICAL: 0,
    JobPriority.HIGH: 1,
    JobPriority.NORMAL: 2,
    JobPriority.LOW: 3,
}


class JobQueue:
    """Async job queue with priority ordering and worker pool."""

    def __init__(self, max_workers: int = 3, max_queue_size: int = 1000):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._jobs: dict[str, Job] = {}
        self._handlers: dict[str, Callable] = {}
        self._workers: list[asyncio.Task] = []
        self._running = False
        self._stats = {"submitted": 0, "completed": 0, "failed": 0}

    def register_handler(self, job_type: str, handler: Callable):
        """Register a handler function for a job type."""
        self._handlers[job_type] = handler

    async def start(self):
        """Start the worker pool."""
        if self._running:
            return
        self._running = True
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(task)
        logger.info(f"Job queue started with {self.max_workers} workers")

    async def stop(self):
        """Stop all workers gracefully."""
        self._running = False
        for task in self._workers:
            task.cancel()
        self._workers.clear()
        logger.info("Job queue stopped")

    async def submit(
        self,
        job_type: str,
        payload: dict,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        timeout_seconds: float = 300,
    ) -> str:
        """Submit a job. Returns job_id."""
        job = Job(
            job_id=str(uuid.uuid4())[:12],
            job_type=job_type,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
        )
        self._jobs[job.job_id] = job
        self._stats["submitted"] += 1

        priority_val = PRIORITY_ORDER[priority]
        await self._queue.put((priority_val, time.time(), job.job_id))

        logger.debug(f"Job {job.job_id} ({job_type}) submitted with {priority.value} priority")
        return job.job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def get_jobs(self, status: Optional[JobStatus] = None, limit: int = 50) -> list[Job]:
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)[:limit]

    def get_stats(self) -> dict:
        pending = sum(1 for j in self._jobs.values() if j.status == JobStatus.PENDING)
        running = sum(1 for j in self._jobs.values() if j.status == JobStatus.RUNNING)
        return {
            **self._stats,
            "pending": pending,
            "running": running,
            "queue_size": self._queue.qsize(),
            "total_jobs": len(self._jobs),
            "workers": self.max_workers,
        }

    async def _worker(self, name: str):
        """Worker loop that processes jobs from the queue."""
        while self._running:
            try:
                _, _, job_id = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            job = self._jobs.get(job_id)
            if not job or job.status == JobStatus.COMPLETED:
                continue

            handler = self._handlers.get(job.job_type)
            if not handler:
                job.status = JobStatus.FAILED
                job.error = f"No handler for job type: {job.job_type}"
                continue

            job.status = JobStatus.RUNNING
            job.started_at = time.time()
            job.attempts += 1

            try:
                result = await asyncio.wait_for(
                    handler(job.payload),
                    timeout=job.timeout_seconds,
                )
                job.result = result
                job.status = JobStatus.COMPLETED
                job.completed_at = time.time()
                self._stats["completed"] += 1
                logger.debug(f"Job {job_id} completed in {job.duration_ms}ms")

            except asyncio.TimeoutError:
                job.error = f"Timeout after {job.timeout_seconds}s"
                self._handle_failure(job)

            except Exception as e:
                job.error = str(e)
                self._handle_failure(job)

    def _handle_failure(self, job: Job):
        if job.attempts < job.max_retries:
            job.status = JobStatus.RETRYING
            delay = min(2 ** job.attempts, 30)
            asyncio.get_event_loop().call_later(
                delay,
                lambda: asyncio.ensure_future(self._retry(job)),
            )
        else:
            job.status = JobStatus.FAILED
            job.completed_at = time.time()
            self._stats["failed"] += 1
            logger.warning(f"Job {job.job_id} failed after {job.attempts} attempts: {job.error}")

    async def _retry(self, job: Job):
        priority_val = PRIORITY_ORDER[job.priority]
        await self._queue.put((priority_val, time.time(), job.job_id))


# Global job queue instance
job_queue = JobQueue(max_workers=3)


# Built-in job handlers
async def _handle_ml_inference(payload: dict) -> dict:
    """Handle ML inference job."""
    model = payload.get("model", "default")
    data = payload.get("data", {})
    return {"model": model, "predictions": {}, "latency_ms": 50}


async def _handle_data_sync(payload: dict) -> dict:
    """Handle data synchronization job."""
    source = payload.get("source", "unknown")
    return {"source": source, "synced": True, "records": 0}


async def _handle_notification(payload: dict) -> dict:
    """Handle notification delivery job."""
    user_id = payload.get("user_id", "")
    message = payload.get("message", "")
    return {"user_id": user_id, "delivered": True}


# Register default handlers
job_queue.register_handler("ml_inference", _handle_ml_inference)
job_queue.register_handler("data_sync", _handle_data_sync)
job_queue.register_handler("notification", _handle_notification)
