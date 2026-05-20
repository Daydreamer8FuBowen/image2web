from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.media_asset import MediaAsset


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def build_dated_dir(self, root: Path, now: datetime | None = None) -> Path:
        current = now or datetime.utcnow()
        target = root / current.strftime("%Y") / current.strftime("%m") / current.strftime("%d")
        target.mkdir(parents=True, exist_ok=True)
        return target

    def build_stored_name(self, suffix: str) -> str:
        clean_suffix = suffix if suffix.startswith(".") else f".{suffix}"
        return f"{datetime.utcnow():%Y%m%d%H%M%S}_{uuid4().hex[:8]}{clean_suffix.lower()}"

    def save_bytes(
        self,
        db: Session,
        *,
        api_key_id: int,
        asset_type: str,
        source_type: str,
        original_name: str,
        mime_type: str,
        content: bytes,
        root_dir: Path,
        task_id: int | None = None,
        record_id: int | None = None,
    ) -> MediaAsset:
        suffix = Path(original_name).suffix or ".png"
        target_dir = self.build_dated_dir(root_dir)
        stored_name = self.build_stored_name(suffix)
        full_path = target_dir / stored_name
        full_path.write_bytes(content)

        asset = MediaAsset(
            api_key_id=api_key_id,
            asset_type=asset_type,
            source_type=source_type,
            original_name=original_name,
            stored_name=stored_name,
            relative_path=str(full_path.relative_to(root_dir.parent)),
            absolute_dir=str(target_dir),
            mime_type=mime_type,
            file_size=len(content),
            task_id=task_id,
            record_id=record_id,
        )
        db.add(asset)
        db.flush()
        return asset

    def public_url(self, asset: MediaAsset) -> str:
        normalized = asset.relative_path.replace("\\", "/")
        return f"/static/{normalized}"
