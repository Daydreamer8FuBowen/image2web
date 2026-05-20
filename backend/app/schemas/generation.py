from datetime import datetime

from pydantic import BaseModel, Field


class InputImageItem(BaseModel):
    id: int
    url: str
    source_type: str
    original_name: str


class GenerationTaskCreateResponse(BaseModel):
    task_id: int
    status: str
    queue_position: int = 0


class GenerationTaskDetailResponse(BaseModel):
    task_id: int
    status: str
    progress_message: str | None = None
    image_url: str | None = None
    remaining_count: int | None = None
    error_message: str | None = None
    input_images: list[InputImageItem] = Field(default_factory=list)
    reference_record_id: int | None = None


class GenerationRecordItem(BaseModel):
    id: int
    prompt: str
    status: str
    image_url: str | None = None
    created_at: datetime
    parent_record_id: int | None = None
