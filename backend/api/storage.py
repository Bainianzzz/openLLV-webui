import imghdr
import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from fastapi import UploadFile

from .errors import APIError

ALLOWED_IMAGES = {
    "jpeg": (".jpg", ".jpeg"),
    "png": (".png",),
    "gif": (".gif",),
    "webp": (".webp",),
}
ALLOWED_MIME = {"image/jpeg", "image/png", "image/gif", "image/webp"}


class ManagedStorage:
    def __init__(self, root: Path, *, max_file_size: int = 20 * 1024 * 1024, max_files: int = 100):
        self.root = root.resolve()
        self.max_file_size = max_file_size
        self.max_files = max_files
        for name in ("uploads", "output", "datasets", "checkpoints", "tmp"):
            (self.root / name).mkdir(parents=True, exist_ok=True)

    def ready(self) -> bool:
        probe = self.root / "tmp" / f".ready-{uuid4().hex}"
        try:
            probe.write_bytes(b"")
            probe.unlink()
            return True
        except OSError:
            return False

    async def save_images(self, files: list[UploadFile]) -> dict:
        if not files:
            raise APIError(400, "invalid_request", "At least one image is required")
        if len(files) > self.max_files:
            raise APIError(400, "invalid_request", "Too many files")

        validated = []
        for upload in files:
            data = await upload.read(self.max_file_size + 1)
            if len(data) > self.max_file_size:
                raise APIError(413, "file_too_large", "Uploaded file is too large")
            image_type = imghdr.what(None, data)
            suffix = Path(upload.filename or "").suffix.lower()
            if (
                upload.content_type not in ALLOWED_MIME
                or image_type not in ALLOWED_IMAGES
                or suffix not in ALLOWED_IMAGES[image_type]
            ):
                raise APIError(415, "unsupported_media_type", "Unsupported image file")
            validated.append((upload.filename or f"image{suffix}", suffix, data))

        artifact_id = str(uuid4())
        if len(validated) == 1:
            display_name, suffix, data = validated[0]
            relative_path = f"{artifact_id}{suffix}"
            target = self.root / "uploads" / relative_path
            self._atomic_write(target, data)
            return {
                "id": artifact_id,
                "relative_path": relative_path,
                "path_type": "file",
                "display_name": Path(display_name).name,
            }

        relative_path = artifact_id
        temporary = self.root / "tmp" / f"upload-{uuid4().hex}"
        target = self.root / "uploads" / relative_path
        temporary.mkdir()
        used_names: set[str] = set()
        try:
            for display_name, suffix, data in validated:
                source_name = Path(display_name).name or f"image{suffix}"
                stem = Path(source_name).stem or "image"
                server_name = source_name
                index = 2
                while server_name in used_names:
                    server_name = f"{stem}-{index}{suffix}"
                    index += 1
                used_names.add(server_name)
                (temporary / server_name).write_bytes(data)
            os.replace(temporary, target)
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        return {
            "id": artifact_id,
            "relative_path": relative_path,
            "path_type": "directory",
            "display_name": f"{len(validated)} images",
        }

    def resolve(self, storage_kind: str, relative_path: str) -> Path:
        candidate = self.target(storage_kind, relative_path)
        if not candidate.exists():
            raise APIError(404, "artifact_not_found", "Artifact does not exist")
        return candidate

    def target(self, storage_kind: str, relative_path: str) -> Path:
        if storage_kind not in {"uploads", "output", "datasets", "checkpoints"}:
            raise APIError(404, "artifact_not_found", "Artifact does not exist")
        root = (self.root / storage_kind).resolve()
        candidate = (root / relative_path).resolve()
        if not candidate.is_relative_to(root) or candidate.is_symlink():
            raise APIError(404, "artifact_not_found", "Artifact does not exist")
        return candidate

    def task_directory(self, storage_kind: str, task_id: str) -> Path:
        path = self.target(storage_kind, task_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def directory_items(self, path: Path) -> list[dict[str, str]]:
        return [{"display_name": item.name} for item in sorted(path.iterdir()) if item.is_file() and not item.is_symlink()]

    @staticmethod
    def _atomic_write(target: Path, data: bytes) -> None:
        with NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            temporary.write(data)
            temporary_path = Path(temporary.name)
        try:
            os.replace(temporary_path, target)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
