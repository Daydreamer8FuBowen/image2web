from fastapi import APIRouter, File, Form, UploadFile

from app.api.deps import ApiKeyHeader, DbSession
from app.schemas.generation import (
    GenerationRecordItem,
    GenerationTaskCreateResponse,
    GenerationTaskDetailResponse,
)
from app.services.generation_service import GenerationService


router = APIRouter(prefix="/api/generations", tags=["generations"])
service = GenerationService()


@router.post("", response_model=GenerationTaskCreateResponse)
async def create_generation_task(
    db: DbSession,
    x_api_key: ApiKeyHeader,
    prompt: str = Form(default=""),
    negative_prompt: str | None = Form(default=None),
    template_id: str | None = Form(default=None),
    reference_record_id: int | None = Form(default=None),
    images: list[UploadFile] = File(default_factory=list),
) -> GenerationTaskCreateResponse:
    return await service.create_task(
        db,
        key_value=x_api_key or "",
        prompt=prompt,
        negative_prompt=negative_prompt,
        template_id=template_id,
        reference_record_id=reference_record_id,
        images=images,
    )


@router.get("/tasks/{task_id}", response_model=GenerationTaskDetailResponse)
def get_task_detail(db: DbSession, x_api_key: ApiKeyHeader, task_id: int) -> GenerationTaskDetailResponse:
    return service.get_task_detail(db, key_value=x_api_key or "", task_id=task_id)


@router.get("/history", response_model=list[GenerationRecordItem])
def get_history(db: DbSession, x_api_key: ApiKeyHeader) -> list[GenerationRecordItem]:
    return service.list_history(db, key_value=x_api_key or "")
