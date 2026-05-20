import asyncio

from app.models.api_key import ApiKey
from app.models.generation_input_image import GenerationInputImage
from app.models.generation_task import GenerationTask
from app.models.media_asset import MediaAsset
from app.providers.base import ProviderResult
from app.services.task_worker_service import TaskWorkerService


class DummyProvider:
    provider_name = "dummy"

    def __init__(self):
        self.received_count = 0

    async def generate_image(self, *, prompt, negative_prompt, input_images):
        self.received_count = len(input_images)
        return ProviderResult(
            remote_url="https://example.com/result.png",
            provider="dummy",
            raw_content="https://example.com/result.png",
        )


class DummyResponse:
    headers = {"content-type": "image/png"}
    content = b"pngdata"

    def raise_for_status(self):
        return None


def test_worker_process_task(monkeypatch, db_session, tmp_path):
    api_key = ApiKey(key_value="user-key-001", name="用户1", remaining_count=3, status="active")
    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)

    stored_dir = tmp_path / "uploads" / "2026" / "05" / "20"
    stored_dir.mkdir(parents=True)
    asset_path = stored_dir / "input.png"
    asset_path.write_bytes(b"input")

    task = GenerationTask(api_key_id=api_key.id, prompt="test", status="pending")
    db_session.add(task)
    db_session.flush()

    asset = MediaAsset(
        api_key_id=api_key.id,
        asset_type="input_image",
        source_type="upload",
        original_name="input.png",
        stored_name="input.png",
        relative_path="uploads/2026/05/20/input.png",
        absolute_dir=str(asset_path.parent),
        mime_type="image/png",
        file_size=5,
        task_id=task.id,
    )
    db_session.add(asset)
    db_session.flush()
    db_session.add(
        GenerationInputImage(task_id=task.id, media_asset_id=asset.id, source_type="upload", sort_order=0)
    )
    db_session.commit()

    dummy_provider = DummyProvider()

    class DummyAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, *args, **kwargs):
            return DummyResponse()

    monkeypatch.setattr("app.services.task_worker_service.get_provider", lambda: dummy_provider)
    monkeypatch.setattr("app.services.task_worker_service.httpx.AsyncClient", DummyAsyncClient)

    worker = TaskWorkerService()
    monkeypatch.setattr(worker.storage_service.settings, "generated_image_dir", tmp_path / "images")
    asyncio.run(worker.execute_task(db_session, db_session.get(GenerationTask, task.id)))

    refreshed_task = db_session.get(GenerationTask, task.id)
    assert refreshed_task.status == "success"
    assert dummy_provider.received_count == 1
