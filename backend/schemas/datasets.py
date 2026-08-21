from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetDownloadCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_key: str
    overwrite: bool = False


class DatasetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    dataset_key: str
    display_name: str
    status: str
    file_count: int | None = None
    total_bytes: int | None = None
    error_code: str | None = None
    created_at: datetime
    updated_at: datetime
