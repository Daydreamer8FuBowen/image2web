from __future__ import annotations

import base64
import json
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

    def extract_provider_error_detail(self, text: str) -> str | None:
        patterns = [
            r"❌\s*[^:：\n]*[:：]\s*(.+)",
            r"(?:图片轮询失败|生成失败|生图失败)[^:：\n]*[:：]\s*(.+)",
        ]
        for pattern in patterns:
            matched = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if matched:
                detail = matched.group(1).strip()
                if detail:
                    return detail
        compact = self._truncate_text(text, 300)
        return compact or None

    def extract_content_text(self, data: dict) -> str:
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {})
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text")
                        if isinstance(text, str):
                            text_parts.append(text)
                if text_parts:
                    return "\n".join(text_parts)

        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message

        raise AppError(PROVIDER_CALL_FAILED, "上游返回格式不符合预期", 502)

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

    def _truncate_text(self, value: str | None, limit: int = 500) -> str | None:
        if value is None:
            return None
        compact = value.strip()
        if len(compact) <= limit:
            return compact
        return f"{compact[:limit]}...<truncated>"

    def _build_request_debug_info(
        self, prompt: str, negative_prompt: str | None, input_images: list[Path]
    ) -> dict:
        return {
            "provider": self.provider_name,
            "url": f"{self.settings.image2_base_url}/v1/chat/completions",
            "model": self.settings.image2_model,
            "timeout_seconds": self.settings.image2_timeout_seconds,
            "prompt_preview": self._truncate_text(prompt, 300),
            "negative_prompt_preview": self._truncate_text(negative_prompt, 300),
            "input_image_count": len(input_images),
            "input_images": [
                {
                    "name": path.name,
                    "suffix": path.suffix.lower(),
                    "exists": path.exists(),
                    "size_bytes": path.stat().st_size if path.exists() else None,
                }
                for path in input_images
            ],
        }

    def _build_response_debug_info(self, response: httpx.Response) -> dict:
        return {
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type"),
            "body_preview": self._truncate_text(response.text, 1000),
        }

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
        request_debug_info = self._build_request_debug_info(prompt, negative_prompt, input_images)
        print(
            f"[Image2Provider] request before call: "
            f"{json.dumps(request_debug_info, ensure_ascii=False, default=str)}"
        )
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
            print(
                f"[Image2Provider] response after call: "
                f"{json.dumps(self._build_response_debug_info(response), ensure_ascii=False)}"
            )
            try:
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise AppError(PROVIDER_CALL_FAILED, f"上游调用失败: {exc}", 502) from exc

        data = response.json()
        content = self.extract_content_text(data)
        image_url = self.extract_image_url(content)
        parsed_log = {
            "choices_count": len(data.get("choices", [])),
            "content_preview": self._truncate_text(content, 1000),
            "extracted_image_url": image_url,
        }
        print(
            f"[Image2Provider] parsed response: "
            f"{json.dumps(parsed_log, ensure_ascii=False)}"
        )
        if not image_url:
            detail = self.extract_provider_error_detail(content)
            raise AppError(IMAGE_URL_NOT_FOUND, detail=detail, status_code=502)

        return ProviderResult(
            remote_url=image_url,
            provider=self.provider_name,
            raw_content=content,
        )
