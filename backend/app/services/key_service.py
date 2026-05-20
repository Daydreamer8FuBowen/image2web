from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, DISABLED_API_KEY, INSUFFICIENT_BALANCE, INVALID_API_KEY
from app.models.api_key import ApiKey


class KeyService:
    def get_active_key(self, db: Session, key_value: str) -> ApiKey:
        statement = select(ApiKey).where(ApiKey.key_value == key_value)
        api_key = db.execute(statement).scalar_one_or_none()
        if api_key is None:
            raise AppError(INVALID_API_KEY, status_code=401)
        if api_key.status != "active":
            raise AppError(DISABLED_API_KEY, status_code=403)
        return api_key

    def validate_generation_access(self, db: Session, key_value: str) -> ApiKey:
        api_key = self.get_active_key(db, key_value)
        if api_key.remaining_count <= 0:
            raise AppError(INSUFFICIENT_BALANCE, status_code=403)
        api_key.last_used_at = datetime.utcnow()
        db.add(api_key)
        db.flush()
        return api_key

    def consume_success_credit(self, db: Session, api_key: ApiKey) -> ApiKey:
        if api_key.remaining_count <= 0:
            raise AppError(INSUFFICIENT_BALANCE, status_code=403)
        api_key.remaining_count -= 1
        api_key.last_used_at = datetime.utcnow()
        db.add(api_key)
        db.flush()
        return api_key
