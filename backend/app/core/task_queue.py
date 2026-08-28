"""
Lightweight async task queue for background ML computations.

Tasks run in the event loop via asyncio.create_task.
Status is tracked in-memory with a simple dict.
"""
import asyncio
import traceback
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, Optional
from pydantic import BaseModel


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskInfo(BaseModel):
    task_id: str
    name: str
    status: TaskStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: float = 0.0  # 0-100


class TaskQueue:
    def __init__(self, max_concurrent: int = 4):
        self.max_concurrent = max_concurrent
        self._tasks: Dict[str, TaskInfo] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active: Dict[str, asyncio.Task] = {}

    async def submit(
        self,
        name: str,
        coro_factory: Callable[[str], Coroutine],
    ) -> str:
        """
        Submit an async task to the queue.
        
        Args:
            name: Human-readable task name
            coro_factory: Async function that takes task_id and returns result
            
        Returns:
            task_id for tracking
        """
        task_id = str(uuid.uuid4())[:8]
        info = TaskInfo(
            task_id=task_id, name=name, status=TaskStatus.PENDING,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._tasks[task_id] = info
        asyncio.create_task(self._run(task_id, coro_factory))
        return task_id

    async def _run(self, task_id: str, coro_factory: Callable):
        info = self._tasks[task_id]
        async with self._semaphore:
            info.status = TaskStatus.RUNNING
            info.started_at = datetime.now(timezone.utc).isoformat()
            try:
                result = await coro_factory(task_id)
                info.result = result
                info.status = TaskStatus.COMPLETED
                info.progress = 100.0
            except Exception as e:
                info.error = f"{type(e).__name__}: {e}"
                info.status = TaskStatus.FAILED
            finally:
                info.completed_at = datetime.now(timezone.utc).isoformat()

    def get(self, task_id: str) -> Optional[TaskInfo]:
        return self._tasks.get(task_id)

    def list_tasks(self, status: Optional[TaskStatus] = None, limit: int = 20) -> list:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)[:limit]

    def cancel(self, task_id: str) -> bool:
        if task_id in self._active:
            self._active[task_id].cancel()
            self._tasks[task_id].status = TaskStatus.FAILED
            self._tasks[task_id].error = "Cancelled"
            return True
        return False

    def stats(self) -> dict:
        by_status = {}
        for t in self._tasks.values():
            by_status[t.status] = by_status.get(t.status, 0) + 1
        return {
            "total": len(self._tasks),
            "by_status": by_status,
            "max_concurrent": self.max_concurrent,
        }


# Global singleton
task_queue = TaskQueue(max_concurrent=4)
