import asyncio

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.services.task_worker_service import TaskWorkerService


class TaskSchedulerService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.worker = TaskWorkerService()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    async def _loop(self) -> None:
        while True:
            db = SessionLocal()
            try:
                await self.worker.run_pending_once(db)
            finally:
                db.close()
            await asyncio.sleep(self.settings.worker_poll_interval_seconds)
