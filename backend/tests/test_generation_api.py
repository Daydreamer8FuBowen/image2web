from io import BytesIO

from app.models.api_key import ApiKey


def seed_key(db_session) -> None:
    db_session.add(ApiKey(key_value="user-key-001", name="用户1", remaining_count=3, status="active"))
    db_session.commit()


def test_create_generation_task(client, db_session):
    seed_key(db_session)
    files = [("images", ("demo.png", BytesIO(b"fakepng"), "image/png"))]
    data = {"prompt": "把背景换成木纹桌面"}

    response = client.post("/api/generations", headers={"X-API-Key": "user-key-001"}, data=data, files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["task_id"] >= 1


def test_reject_fourth_upload_image(client, db_session):
    seed_key(db_session)
    files = [
        ("images", ("1.png", BytesIO(b"a"), "image/png")),
        ("images", ("2.png", BytesIO(b"b"), "image/png")),
        ("images", ("3.png", BytesIO(b"c"), "image/png")),
        ("images", ("4.png", BytesIO(b"d"), "image/png")),
    ]

    response = client.post(
        "/api/generations",
        headers={"X-API-Key": "user-key-001"},
        data={"prompt": "test"},
        files=files,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "GEN_001"
