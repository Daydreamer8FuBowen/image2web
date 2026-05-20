from __future__ import annotations

import base64
import re
from pathlib import Path

import httpx

from app.core.config import get_settings
from app.core.errors import AppError, IMAGE_URL_NOT_FOUND, PROVIDER_CALL_FAILED
from app.providers.base import BaseImageProvider, ProviderResult


class Image2Provider(BaseImageProvider):
    provider_name = "image2"

    def __init__(self) -> None:
        self.settings = get_settings()

    def extract_image_url(self, text: str) -> str | None:
        patterns = [
            r"!\[[^\]]*?\]\((https?://[^\s)]+?\.(?:png|jpg|jpeg|gif|webp)(?:\?[^\s)]*)?)\)",
            r"\[[^\]]*?\]\((https?://[^\s)]+?\.(?:png|jpg|jpeg|gif|webp)(?:\?[^\s)]*)?)\)",
            r"(https?://[^\s\]\)]+?\.(?:png|jpg|jpeg|gif|webp)(?:\?[^\s\]\)]*)?)",
        ]
        for pattern in patterns:
            matched = re.search(pattern, text, re.IGNORECASE)
            if matched:
                return matched.group(1)
        return None

    def image_to_base64(self, image_path: Path) -> str:
        suffix = image_path.suffix.lower()
        mime = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }.get(suffix)
        if mime is None:
            raise AppError(PROVIDER_CALL_FAILED, f"不支持的图片格式: {suffix}", 400)
        encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        return f"data:{mime};base64,{encoded}"

    def build_messages(
        self, prompt: str, negative_prompt: str | None, input_images: list[Path]
    ) -> list[dict]:
        final_prompt = prompt.strip()
        if negative_prompt:
            final_prompt = f"{final_prompt}\n\n负向要求：{negative_prompt.strip()}"

        content: list[dict] = [{"type": "text", "text": final_prompt}]
        for path in input_images:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": self.image_to_base64(path)},
                }
            )
        return [{"role": "user", "content": content}]

    async def generate_image(
        self,
        *,
        prompt: str,
        negative_prompt: str | None,
        input_images: list[Path],
    ) -> ProviderResult:
        headers = {
            "Authorization": f"Bearer {self.settings.image2_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.settings.image2_model,
            "messages": self.build_messages(prompt, negative_prompt, input_images),
            "max_tokens": 3000,
        }
        async with httpx.AsyncClient(timeout=self.settings.image2_timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.image2_base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            try:
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise AppError(PROVIDER_CALL_FAILED, f"上游调用失败: {exc}", 502) from exc

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        image_url = self.extract_image_url(content)
        if not image_url:
            raise AppError(IMAGE_URL_NOT_FOUND, status_code=502)

        return ProviderResult(
            remote_url=image_url,
            provider=self.provider_name,
            raw_content=content,
        )
