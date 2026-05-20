from app.models.api_key import ApiKey
from app.models.generation_input_image import GenerationInputImage
from app.models.generation_record import GenerationRecord
from app.models.generation_task import GenerationTask
from app.models.media_asset import MediaAsset


ADMIN_HEADERS = {"X-API-Key": "admin-test-key"}


def test_admin_me(client):
    response = client.get("/api/admin/me", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["is_admin"] is True


def test_admin_create_and_list_keys(client):
    create_response = client.post(
        "/api/admin/keys",
        headers=ADMIN_HEADERS,
        json={"name": "用户A", "key_value": "user-a", "remaining_count": 5},
    )
    assert create_response.status_code == 200
    assert create_response.json()["name"] == "用户A"

    list_response = client.get("/api/admin/keys", headers=ADMIN_HEADERS)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_admin_stats(client, db_session):
    db_session.add(ApiKey(key_value="user-x", name="用户X", remaining_count=1, status="active"))
    db_session.commit()

    response = client.get("/api/admin/stats", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["total_keys"] == 1


def test_admin_recharge_key(client, db_session):
    api_key = ApiKey(key_value="user-recharge", name="用户充值", remaining_count=2, status="active")
    db_session.add(api_key)
    db_session.commit()

    response = client.patch(
        f"/api/admin/keys/{api_key.id}/recharge",
        headers=ADMIN_HEADERS,
        json={"delta": 5},
    )
    assert response.status_code == 200
    assert response.json()["remaining_count"] == 7


def test_admin_list_key_records(client, db_session):
    api_key = ApiKey(key_value="user-record", name="用户记录", remaining_count=5, status="active")
    db_session.add(api_key)
    db_session.flush()

    record_asset = MediaAsset(
        api_key_id=api_key.id,
        asset_type="result_image",
        source_type="generation",
        original_name="result.png",
        stored_name="result.png",
        relative_path="images/2026/05/20/result.png",
        absolute_dir="E:/codes/image2web/data/images/2026/05/20",
        mime_type="image/png",
        file_size=123,
    )
    db_session.add(record_asset)
    db_session.flush()

    record = GenerationRecord(
        api_key_id=api_key.id,
        prompt="夜景城市海报",
        negative_prompt="低清晰度",
        status="success",
        result_media_asset_id=record_asset.id,
    )
    db_session.add(record)
    db_session.flush()

    task = GenerationTask(
        api_key_id=api_key.id,
        prompt="夜景城市海报",
        negative_prompt="低清晰度",
        status="success",
        result_record_id=record.id,
    )
    db_session.add(task)
    db_session.flush()

    input_asset = MediaAsset(
        api_key_id=api_key.id,
        asset_type="input_image",
        source_type="upload",
        original_name="input.png",
        stored_name="input.png",
        relative_path="uploads/2026/05/20/input.png",
        absolute_dir="E:/codes/image2web/data/uploads/2026/05/20",
        mime_type="image/png",
        file_size=88,
        task_id=task.id,
    )
    db_session.add(input_asset)
    db_session.flush()

    db_session.add(
        GenerationInputImage(
            task_id=task.id,
            media_asset_id=input_asset.id,
            source_type="upload",
            sort_order=0,
        )
    )
    db_session.commit()

    response = client.get(f"/api/admin/keys/{api_key.id}/records", headers=ADMIN_HEADERS)
    assert response.status_code == 200

    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["prompt"] == "夜景城市海报"
    assert payload[0]["image_url"] == "/static/images/2026/05/20/result.png"
    assert payload[0]["input_images"][0]["url"] == "/static/uploads/2026/05/20/input.png"


def test_admin_delete_key(client, db_session):
    api_key = ApiKey(key_value="user-delete", name="待删除用户", remaining_count=3, status="active")
    db_session.add(api_key)
    db_session.commit()

    response = client.delete(f"/api/admin/keys/{api_key.id}", headers=ADMIN_HEADERS)
    assert response.status_code == 204

    list_response = client.get("/api/admin/keys", headers=ADMIN_HEADERS)
    assert list_response.status_code == 200
    assert list_response.json() == []
