from hmac import compare_digest

from app.core.config import get_settings
from app.core.errors import AppError, UNAUTHORIZED_ADMIN


class AdminAuthService:
    def validate_admin_key(self, key_value: str | None) -> None:
        settings = get_settings()
        expected = settings.admin_login_key or ""
        provided = key_value or ""
        if not expected or not compare_digest(expected, provided):
            raise AppError(UNAUTHORIZED_ADMIN, status_code=401)
