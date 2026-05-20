from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProviderResult:
    remote_url: str
    provider: str
    raw_content: str


class BaseImageProvider:
    provider_name = "base"

    async def generate_image(
        self,
        *,
        prompt: str,
        negative_prompt: str | None,
        input_images: list[Path],
    ) -> ProviderResult:
        raise NotImplementedError
