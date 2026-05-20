from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.models.api_key import ApiKey
from app.models.generation_input_image import GenerationInputImage
from app.models.generation_record import GenerationRecord
from app.models.generation_task import GenerationTask
from app.models.media_asset import MediaAsset
from app.providers.factory import get_provider
from app.services.key_service import KeyService
from app.services.storage_service import StorageService


class TaskWorkerService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.storage_service = StorageService()
        self.key_service = KeyService()

    async def run_pending_once(self, db: Session) -> GenerationTask | None:
        statement = (
            select(GenerationTask)
            .where(GenerationTask.status == "pending")
            .order_by(GenerationTask.created_at.asc())
        )
        task = db.execute(statement).scalar_one_or_none()
        if task is None:
            return None
        await self.execute_task(db, task)
        return task

    async def execute_task(self, db: Session, task: GenerationTask) -> GenerationTask:
        provider = get_provider()
        task.status = "processing"
        task.progress_message = "正在调用生成接口"
        task.started_at = datetime.utcnow()
        db.add(task)
        db.commit()
        db.refresh(task)

        try:
            input_assets = self._load_input_assets(db, task.id)
            input_paths = [Path(asset.absolute_dir) / asset.stored_name for asset in input_assets]
            start_log = {
                "task_id": task.id,
                "api_key_id": task.api_key_id,
                "prompt_preview": task.prompt[:300],
                "negative_prompt_preview": task.negative_prompt[:300] if task.negative_prompt else None,
                "input_image_count": len(input_paths),
                "input_images": [str(path) for path in input_paths],
            }
            print(
                f"[TaskWorkerService] provider call start: "
                f"{json.dumps(start_log, ensure_ascii=False)}"
            )
            result = await provider.generate_image(
                prompt=task.prompt,
                negative_prompt=task.negative_prompt,
                input_images=input_paths,
            )
            end_log = {
                "task_id": task.id,
                "provider": result.provider,
                "remote_url": result.remote_url,
                "raw_content_preview": result.raw_content[:1000],
            }
            print(
                f"[TaskWorkerService] provider call end: "
                f"{json.dumps(end_log, ensure_ascii=False)}"
            )
            async with httpx.AsyncClient(timeout=120.0) as client:
                remote = await client.get(result.remote_url)
                remote.raise_for_status()

            generated_asset = self.storage_service.save_bytes(
                db,
                api_key_id=task.api_key_id,
                asset_type="generated_image",
                source_type="generation_result",
                original_name="generated.png",
                mime_type=remote.headers.get("content-type", "image/png"),
                content=remote.content,
                root_dir=self.settings.generated_image_dir,
                task_id=task.id,
            )

            record = GenerationRecord(
                api_key_id=task.api_key_id,
                prompt=task.prompt,
                negative_prompt=task.negative_prompt,
                template_id=task.template_id,
                status="success",
                result_media_asset_id=generated_asset.id,
                provider=result.provider,
            )
            db.add(record)
            db.flush()

            generated_asset.record_id = record.id
            db.add(generated_asset)

            api_key = db.get(ApiKey, task.api_key_id)
            if api_key is not None:
                self.key_service.consume_success_credit(db, api_key)

            task.status = "success"
            task.progress_message = "图片生成完成"
            task.result_record_id = record.id
            task.finished_at = datetime.utcnow()
            db.add(task)
            db.commit()
            db.refresh(task)
            return task
        except Exception as exc:
            db.rollback()
            error_log = {
                "task_id": task.id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
            print(
                f"[TaskWorkerService] provider call failed: "
                f"{json.dumps(error_log, ensure_ascii=False)}"
            )
            if isinstance(exc, AppError):
                task.error_message = exc.detail
            else:
                task.error_message = str(exc)
            task.status = "failed"
            task.progress_message = "图片生成失败"
            task.finished_at = datetime.utcnow()
            db.add(task)
            db.commit()
            db.refresh(task)
            return task

    def _load_input_assets(self, db: Session, task_id: int) -> list[MediaAsset]:
        statement = (
            select(MediaAsset)
            .join(GenerationInputImage, GenerationInputImage.media_asset_id == MediaAsset.id)
            .where(GenerationInputImage.task_id == task_id)
            .order_by(GenerationInputImage.sort_order.asc())
        )
        return list(db.execute(statement).scalars().all())
