import pytest

from app.core.errors import AppError
from app.models.api_key import ApiKey
from app.services.admin_auth_service import AdminAuthService
from app.services.key_service import KeyService


def seed_key(db_session, *, remaining_count: int = 3, status: str = "active") -> ApiKey:
    api_key = ApiKey(
        key_value="user-key-001",
        name="测试 Key",
        remaining_count=remaining_count,
        status=status,
    )
    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)
    return api_key


def test_validate_generation_access_success(db_session):
    seed_key(db_session, remaining_count=2)
    service = KeyService()

    api_key = service.validate_generation_access(db_session, "user-key-001")

    assert api_key.name == "测试 Key"
    assert api_key.remaining_count == 2


def test_validate_generation_access_balance_exhausted(db_session):
    seed_key(db_session, remaining_count=0)
    service = KeyService()

    with pytest.raises(AppError) as exc_info:
        service.validate_generation_access(db_session, "user-key-001")

    assert exc_info.value.error_code.code == "AUTH_002"


def test_validate_generation_access_disabled_key(db_session):
    seed_key(db_session, status="disabled")
    service = KeyService()

    with pytest.raises(AppError) as exc_info:
        service.validate_generation_access(db_session, "user-key-001")

    assert exc_info.value.error_code.code == "AUTH_003"


def test_admin_auth_service_accepts_configured_key():
    AdminAuthService().validate_admin_key("admin-test-key")


def test_admin_auth_service_rejects_invalid_key():
    with pytest.raises(AppError) as exc_info:
        AdminAuthService().validate_admin_key("wrong-key")

    assert exc_info.value.error_code.code == "AUTH_004"
