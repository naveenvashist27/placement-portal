import uuid
from pathlib import Path

from app.core.config import get_settings


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def upload(self, folder: str, filename: str, data: bytes, content_type: str) -> str:
        if self.settings.supabase_url and self.settings.supabase_service_role_key:
            return await self._upload_supabase(folder, filename, data, content_type)
        return self._upload_local(folder, filename, data)

    def _upload_local(self, folder: str, filename: str, data: bytes) -> str:
        base = Path(self.settings.local_storage_path) / folder
        base.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex}_{filename}"
        path = base / safe_name
        path.write_bytes(data)
        return str(path.as_posix())

    async def _upload_supabase(self, folder: str, filename: str, data: bytes, content_type: str) -> str:
        from supabase import create_client

        client = create_client(self.settings.supabase_url, self.settings.supabase_service_role_key)
        safe_name = f"{folder}/{uuid.uuid4().hex}_{filename}"
        bucket = self.settings.supabase_storage_bucket
        client.storage.from_(bucket).upload(safe_name, data, {"content-type": content_type})
        return safe_name

    def public_url(self, path: str) -> str:
        if self.settings.supabase_url and not path.startswith(str(Path(self.settings.local_storage_path))):
            bucket = self.settings.supabase_storage_bucket
            return f"{self.settings.supabase_url}/storage/v1/object/public/{bucket}/{path}"
        return f"/static/{path}"
