import asyncio
import json

import pytest

from app.core.errors import AppError
from app.providers.image2_provider import Image2Provider


class DummyResponse:
    def __init__(self, payload: dict):
        self._payload = payload
        self.status_code = 200
        self.headers = {"content-type": "application/json; charset=utf-8"}
        self.text = json.dumps(payload, ensure_ascii=False)

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_extract_image_url_from_markdown():
    provider = Image2Provider()

    content = "![result](https://example.com/output/result-image.png)"

    assert provider.extract_image_url(content) == "https://example.com/output/result-image.png"


def test_generate_image_returns_upstream_error_detail(monkeypatch):
    provider = Image2Provider()
    payload = {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1779263658,
        "model": "gpt-image-2",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": (
                        "> 🎨 生成中...\n\n"
                        "> ❌ 图片轮询失败: 生图失败（敏感检测 / 内容安全策略命中（policy））: "
                        "We’re so sorry, but the prompt may violate our guardrails "
                        "concerning similarity to third-party content."
                    ),
                },
                "finish_reason": "stop",
            }
        ],
    }

    class DummyAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, *args, **kwargs):
            return DummyResponse(payload)

    monkeypatch.setattr("app.providers.image2_provider.httpx.AsyncClient", DummyAsyncClient)

    with pytest.raises(AppError) as exc_info:
        asyncio.run(
            provider.generate_image(
                prompt="test prompt",
                negative_prompt=None,
                input_images=[],
            )
        )

    assert exc_info.value.detail == (
        "生图失败（敏感检测 / 内容安全策略命中（policy））: "
        "We’re so sorry, but the prompt may violate our guardrails "
        "concerning similarity to third-party content."
    )
