from datetime import datetime

from pydantic import BaseModel, Field


class ApiKeyCreateRequest(BaseModel):
    name: str
    key_value: str
    remaining_count: int


class ApiKeyRechargeRequest(BaseModel):
    delta: int


class ApiKeyStatusRequest(BaseModel):
    status: str


class ApiKeyItem(BaseModel):
    id: int
    name: str
    key_value: str
    remaining_count: int
    status: str
    created_at: datetime


class AdminRecordInputImageItem(BaseModel):
    id: int
    url: str
    source_type: str
    original_name: str


class AdminRecordItem(BaseModel):
    id: int
    prompt: str
    negative_prompt: str | None = None
    status: str
    image_url: str | None = None
    created_at: datetime
    parent_record_id: int | None = None
    input_images: list[AdminRecordInputImageItem] = Field(default_factory=list)


class AdminStatsResponse(BaseModel):
    total_keys: int
    total_tasks: int
    processing_tasks: int
    success_records: int
    failed_tasks: int
