import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test.db")
os.environ.setdefault("ADMIN_LOGIN_KEY", "admin-test-key")

from app.core.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


TEST_DB_URL = "sqlite:///./data/test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def reset_database() -> None:
    Base.metadata.create_all(bind=engine)
    yield
    cleanup_order = [
        "generation_input_images",
        "admin_audits",
        "generation_tasks",
        "generation_records",
        "media_assets",
        "api_keys",
    ]
    with engine.begin() as connection:
        for table_name in cleanup_order:
            table = Base.metadata.tables.get(table_name)
            if table is not None:
                connection.execute(table.delete())


@pytest.fixture
def db_session() -> Session:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
