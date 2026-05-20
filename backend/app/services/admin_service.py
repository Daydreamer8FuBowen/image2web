from pathlib import Path

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.models.api_key import ApiKey
from app.models.generation_input_image import GenerationInputImage
from app.models.generation_record import GenerationRecord
from app.models.generation_task import GenerationTask
from app.models.media_asset import MediaAsset
from app.schemas.admin import (
    AdminRecordInputImageItem,
    AdminRecordItem,
    AdminStatsResponse,
    ApiKeyCreateRequest,
    ApiKeyItem,
    ApiKeyRechargeRequest,
    ApiKeyStatusRequest,
)
from app.services.storage_service import StorageService


class AdminService:
    def __init__(self) -> None:
        self.storage_service = StorageService()

    def create_key(self, db: Session, payload: ApiKeyCreateRequest) -> ApiKey:
        api_key = ApiKey(
            name=payload.name,
            key_value=payload.key_value,
            remaining_count=payload.remaining_count,
            status="active",
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key

    def list_keys(self, db: Session) -> list[ApiKeyItem]:
        statement = select(ApiKey).order_by(ApiKey.created_at.desc())
        rows = db.execute(statement).scalars().all()
        return [
            ApiKeyItem(
                id=item.id,
                name=item.name,
                key_value=item.key_value,
                remaining_count=item.remaining_count,
                status=item.status,
                created_at=item.created_at,
            )
            for item in rows
        ]

    def recharge_key(self, db: Session, key_id: int, payload: ApiKeyRechargeRequest) -> ApiKey:
        api_key = db.get(ApiKey, key_id)
        if api_key is None:
            raise ValueError("api key not found")
        api_key.remaining_count += payload.delta
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key

    def update_key_status(self, db: Session, key_id: int, payload: ApiKeyStatusRequest) -> ApiKey:
        api_key = db.get(ApiKey, key_id)
        if api_key is None:
            raise ValueError("api key not found")
        api_key.status = payload.status
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key

    def delete_key(self, db: Session, key_id: int) -> None:
        api_key = db.get(ApiKey, key_id)
        if api_key is None:
            raise ValueError("api key not found")

        task_ids = db.scalars(select(GenerationTask.id).where(GenerationTask.api_key_id == key_id)).all()
        record_ids = db.scalars(select(GenerationRecord.id).where(GenerationRecord.api_key_id == key_id)).all()
        media_assets = db.scalars(select(MediaAsset).where(MediaAsset.api_key_id == key_id)).all()
        media_ids = [asset.id for asset in media_assets]

        if record_ids:
            db.execute(
                update(GenerationTask)
                .where(GenerationTask.result_record_id.in_(record_ids))
                .values(result_record_id=None)
            )
            db.execute(
                update(GenerationInputImage)
                .where(GenerationInputImage.source_record_id.in_(record_ids))
                .values(source_record_id=None)
            )
            db.execute(
                update(GenerationRecord)
                .where(GenerationRecord.parent_record_id.in_(record_ids))
                .values(parent_record_id=None)
            )

        if media_ids:
            db.execute(
                update(GenerationRecord)
                .where(GenerationRecord.result_media_asset_id.in_(media_ids))
                .values(result_media_asset_id=None)
            )

        if task_ids:
            db.execute(delete(GenerationInputImage).where(GenerationInputImage.task_id.in_(task_ids)))

        for asset in media_assets:
            file_path = Path(asset.absolute_dir) / asset.stored_name
            if file_path.exists():
                file_path.unlink()

        db.execute(delete(MediaAsset).where(MediaAsset.api_key_id == key_id))
        db.execute(delete(GenerationTask).where(GenerationTask.api_key_id == key_id))
        db.execute(delete(GenerationRecord).where(GenerationRecord.api_key_id == key_id))
        db.delete(api_key)
        db.commit()

    def list_key_records(self, db: Session, key_id: int) -> list[AdminRecordItem]:
        api_key = db.get(ApiKey, key_id)
        if api_key is None:
            raise ValueError("api key not found")

        statement = (
            select(GenerationRecord, MediaAsset)
            .outerjoin(MediaAsset, MediaAsset.id == GenerationRecord.result_media_asset_id)
            .where(GenerationRecord.api_key_id == key_id)
            .order_by(GenerationRecord.created_at.desc())
        )
        rows = db.execute(statement).all()
        records = [record for record, _ in rows]
        record_ids = [record.id for record in records]

        input_images_by_record: dict[int, list[AdminRecordInputImageItem]] = {
            record_id: [] for record_id in record_ids
        }
        if record_ids:
            input_rows = db.execute(
                select(GenerationTask.result_record_id, GenerationInputImage, MediaAsset)
                .join(GenerationInputImage, GenerationInputImage.task_id == GenerationTask.id)
                .join(MediaAsset, MediaAsset.id == GenerationInputImage.media_asset_id)
                .where(GenerationTask.result_record_id.in_(record_ids))
                .order_by(GenerationTask.result_record_id.asc(), GenerationInputImage.sort_order.asc())
            ).all()
            for record_id, relation, asset in input_rows:
                if record_id is None:
                    continue
                input_images_by_record.setdefault(record_id, []).append(
                    AdminRecordInputImageItem(
                        id=asset.id,
                        url=self.storage_service.public_url(asset),
                        source_type=relation.source_type,
                        original_name=asset.original_name,
                    )
                )

        return [
            AdminRecordItem(
                id=record.id,
                prompt=record.prompt,
                negative_prompt=record.negative_prompt,
                status=record.status,
                image_url=self.storage_service.public_url(asset) if asset else None,
                created_at=record.created_at,
                parent_record_id=record.parent_record_id,
                input_images=input_images_by_record.get(record.id, []),
            )
            for record, asset in rows
        ]

    def build_stats(self, db: Session) -> AdminStatsResponse:
        total_keys = db.scalar(select(func.count()).select_from(ApiKey)) or 0
        total_tasks = db.scalar(select(func.count()).select_from(GenerationTask)) or 0
        processing_tasks = (
            db.scalar(select(func.count()).select_from(GenerationTask).where(GenerationTask.status == "processing"))
            or 0
        )
        success_records = (
            db.scalar(
                select(func.count()).select_from(GenerationRecord).where(GenerationRecord.status == "success")
            )
            or 0
        )
        failed_tasks = (
            db.scalar(select(func.count()).select_from(GenerationTask).where(GenerationTask.status == "failed"))
            or 0
        )
        return AdminStatsResponse(
            total_keys=total_keys,
            total_tasks=total_tasks,
            processing_tasks=processing_tasks,
            success_records=success_records,
            failed_tasks=failed_tasks,
        )
