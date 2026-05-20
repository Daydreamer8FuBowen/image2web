from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.admin_auth_service import AdminAuthService


DbSession = Annotated[Session, Depends(get_db)]
ApiKeyHeader = Annotated[str | None, Header(alias="X-API-Key")]


def require_admin_key(x_api_key: ApiKeyHeader) -> str:
    AdminAuthService().validate_admin_key(x_api_key)
    return x_api_key or ""
