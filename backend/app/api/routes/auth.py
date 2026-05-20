from fastapi import APIRouter

from app.api.deps import ApiKeyHeader, DbSession
from app.schemas.auth import UserAuthInfo
from app.services.key_service import KeyService


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=UserAuthInfo)
def auth_me(db: DbSession, x_api_key: ApiKeyHeader) -> UserAuthInfo:
    api_key = KeyService().get_active_key(db, x_api_key or "")
    return UserAuthInfo(
        key_name=api_key.name,
        remaining_count=api_key.remaining_count,
        status=api_key.status,
    )
