from pathlib import Path

from app.core.config import Settings


def test_settings_fall_back_to_env_example(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("ADMIN_LOGIN_KEY", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    env_example = tmp_path / ".env.example"
    env_example.write_text("ADMIN_LOGIN_KEY=example-admin\nAPP_ENV=example\n", encoding="utf-8")

    settings = Settings(_env_file=(env_example, tmp_path / ".env"))

    assert settings.admin_login_key == "example-admin"
    assert settings.app_env == "example"


def test_settings_prefer_env_over_env_example(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("ADMIN_LOGIN_KEY", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("ADMIN_LOGIN_KEY=real-admin\nAPP_ENV=prod\n", encoding="utf-8")
    env_example = tmp_path / ".env.example"
    env_example.write_text("ADMIN_LOGIN_KEY=example-admin\nAPP_ENV=example\n", encoding="utf-8")

    settings = Settings(_env_file=(env_example, env_file))

    assert settings.admin_login_key == "real-admin"
    assert settings.app_env == "prod"
