from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_admin_key
from app.schemas.admin import (
    AdminRecordItem,
    AdminStatsResponse,
    ApiKeyCreateRequest,
    ApiKeyItem,
    ApiKeyRechargeRequest,
    ApiKeyStatusRequest,
)
from app.schemas.auth import AdminAuthInfo
from app.services.admin_service import AdminService


router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin_key)])
service = AdminService()


@router.get("/me", response_model=AdminAuthInfo)
def admin_me() -> AdminAuthInfo:
    return AdminAuthInfo()


@router.get("/keys", response_model=list[ApiKeyItem])
def list_keys(db: DbSession) -> list[ApiKeyItem]:
    return service.list_keys(db)


@router.get("/keys/{key_id}/records", response_model=list[AdminRecordItem])
def list_key_records(db: DbSession, key_id: int) -> list[AdminRecordItem]:
    return service.list_key_records(db, key_id)


@router.post("/keys", response_model=ApiKeyItem)
def create_key(db: DbSession, payload: ApiKeyCreateRequest) -> ApiKeyItem:
    item = service.create_key(db, payload)
    return ApiKeyItem.model_validate(item, from_attributes=True)


@router.patch("/keys/{key_id}/recharge", response_model=ApiKeyItem)
def recharge_key(db: DbSession, key_id: int, payload: ApiKeyRechargeRequest) -> ApiKeyItem:
    item = service.recharge_key(db, key_id, payload)
    return ApiKeyItem.model_validate(item, from_attributes=True)


@router.patch("/keys/{key_id}/status", response_model=ApiKeyItem)
def update_key_status(db: DbSession, key_id: int, payload: ApiKeyStatusRequest) -> ApiKeyItem:
    item = service.update_key_status(db, key_id, payload)
    return ApiKeyItem.model_validate(item, from_attributes=True)


@router.delete("/keys/{key_id}", status_code=204)
def delete_key(db: DbSession, key_id: int) -> None:
    service.delete_key(db, key_id)


@router.get("/stats", response_model=AdminStatsResponse)
def get_stats(db: DbSession) -> AdminStatsResponse:
    return service.build_stats(db)
