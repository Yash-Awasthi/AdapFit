"""
AdapFit Background Task Queue
Non-blocking background tasks using asyncio.create_task.
For LLM calls, post-workout processing, and periodic maintenance.
"""
import asyncio
import logging
from typing import Callable, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("adapfit.background")


class BackgroundTaskManager:
    """Simple in-process background task manager."""

    def __init__(self):
        self._tasks: dict[str, asyncio.Task] = {}
        self._completed: list[dict] = []

    async def submit(self, name: str, coro_fn: Callable, *args, **kwargs) -> str:
        """Submit a background task. Returns task ID."""
        task_id = f"{name}_{datetime.now(timezone.utc).strftime('%H%M%S%f')}"

        async def wrapper():
            start = datetime.now(timezone.utc)
            try:
                result = await coro_fn(*args, **kwargs)
                elapsed = (datetime.now(timezone.utc) - start).total_seconds()
                self._completed.append({
                    "task_id": task_id,
                    "name": name,
                    "status": "completed",
                    "elapsed_seconds": round(elapsed, 2),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                })
                logger.info(f"Background task {task_id} completed in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = (datetime.now(timezone.utc) - start).total_seconds()
                self._completed.append({
                    "task_id": task_id,
                    "name": name,
                    "status": "failed",
                    "error": str(e),
                    "elapsed_seconds": round(elapsed, 2),
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                })
                logger.error(f"Background task {task_id} failed: {e}")
                return None
            finally:
                self._tasks.pop(task_id, None)

        task = asyncio.create_task(wrapper())
        self._tasks[task_id] = task
        return task_id

    def get_status(self) -> dict:
        """Get task manager status."""
        return {
            "active_tasks": len(self._tasks),
            "completed_tasks": len(self._completed),
            "recent_completions": self._completed[-5:] if self._completed else [],
        }

    async def cancel(self, task_id: str) -> bool:
        """Cancel a running task."""
        task = self._tasks.get(task_id)
        if task and not task.done():
            task.cancel()
            return True
        return False


# Singleton
task_manager = BackgroundTaskManager()
