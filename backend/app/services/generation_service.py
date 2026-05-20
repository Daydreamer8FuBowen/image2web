from __future__ import annotations

from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import (
    AppError,
    EMPTY_GENERATION_INPUT,
    IMAGE_FORMAT_INVALID,
    IMAGE_LIMIT_EXCEEDED,
    IMAGE_TOO_LARGE,
    TASK_NOT_FOUND,
)
from app.models.generation_input_image import GenerationInputImage
from app.models.generation_record import GenerationRecord
from app.models.generation_task import GenerationTask
from app.models.media_asset import MediaAsset
from app.schemas.generation import (
    GenerationRecordItem,
    GenerationTaskCreateResponse,
    GenerationTaskDetailResponse,
    InputImageItem,
)
from app.services.key_service import KeyService
from app.services.storage_service import StorageService


class GenerationService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.key_service = KeyService()
        self.storage_service = StorageService()
        self.allowed_suffixes = {".png", ".jpg", ".jpeg", ".webp"}

    async def create_task(
        self,
        db: Session,
        *,
        key_value: str,
        prompt: str,
        negative_prompt: str | None,
        template_id: str | None,
        reference_record_id: int | None,
        images: list[UploadFile],
    ) -> GenerationTaskCreateResponse:
        if len(images) > self.settings.max_upload_images:
            raise AppError(IMAGE_LIMIT_EXCEEDED, status_code=400)
        if not prompt.strip() and not images:
            raise AppError(EMPTY_GENERATION_INPUT, status_code=400)

        api_key = self.key_service.validate_generation_access(db, key_value)
        task = GenerationTask(
            api_key_id=api_key.id,
            prompt=prompt.strip(),
            negative_prompt=(negative_prompt or "").strip() or None,
            template_id=template_id,
            status="pending",
            progress_message="任务已提交",
        )
        db.add(task)
        db.flush()

        for index, upload in enumerate(images):
            content = await upload.read()
            suffix = Path(upload.filename or "").suffix.lower()
            if suffix not in self.allowed_suffixes:
                raise AppError(IMAGE_FORMAT_INVALID, status_code=400)
            if len(content) > self.settings.max_upload_bytes:
                raise AppError(IMAGE_TOO_LARGE, status_code=400)

            asset = self.storage_service.save_bytes(
                db,
                api_key_id=api_key.id,
                asset_type="input_image",
                source_type="upload",
                original_name=upload.filename or f"upload_{index}{suffix}",
                mime_type=upload.content_type or "application/octet-stream",
                content=content,
                root_dir=self.settings.upload_image_dir,
                task_id=task.id,
            )
            db.add(
                GenerationInputImage(
                    task_id=task.id,
                    media_asset_id=asset.id,
                    source_type="upload",
                    sort_order=index,
                    source_record_id=reference_record_id,
                )
            )

        db.commit()
        return GenerationTaskCreateResponse(task_id=task.id, status=task.status, queue_position=0)

    def get_task_detail(self, db: Session, *, key_value: str, task_id: int) -> GenerationTaskDetailResponse:
        api_key = self.key_service.get_active_key(db, key_value)
        task = db.get(GenerationTask, task_id)
        if task is None or task.api_key_id != api_key.id:
            raise AppError(TASK_NOT_FOUND, status_code=404)

        inputs = db.execute(
            select(GenerationInputImage, MediaAsset)
            .join(MediaAsset, MediaAsset.id == GenerationInputImage.media_asset_id)
            .where(GenerationInputImage.task_id == task.id)
            .order_by(GenerationInputImage.sort_order.asc())
        ).all()
        input_images = [
            InputImageItem(
                id=asset.id,
                url=self.storage_service.public_url(asset),
                source_type=relation.source_type,
                original_name=asset.original_name,
            )
            for relation, asset in inputs
        ]

        image_url = None
        remaining_count = api_key.remaining_count
        if task.result_record_id:
            record = db.get(GenerationRecord, task.result_record_id)
            if record and record.result_media_asset_id:
                asset = db.get(MediaAsset, record.result_media_asset_id)
                if asset:
                    image_url = self.storage_service.public_url(asset)

        return GenerationTaskDetailResponse(
            task_id=task.id,
            status=task.status,
            progress_message=task.progress_message,
            image_url=image_url,
            remaining_count=remaining_count,
            error_message=task.error_message,
            input_images=input_images,
        )

    def list_history(self, db: Session, *, key_value: str) -> list[GenerationRecordItem]:
        api_key = self.key_service.get_active_key(db, key_value)
        statement = (
            select(GenerationRecord, MediaAsset)
            .outerjoin(MediaAsset, MediaAsset.id == GenerationRecord.result_media_asset_id)
            .where(GenerationRecord.api_key_id == api_key.id)
            .order_by(GenerationRecord.created_at.desc())
        )
        rows = db.execute(statement).all()
        return [
            GenerationRecordItem(
                id=record.id,
                prompt=record.prompt,
                status=record.status,
                image_url=self.storage_service.public_url(asset) if asset else None,
                created_at=record.created_at,
                parent_record_id=record.parent_record_id,
            )
            for record, asset in rows
        ]
