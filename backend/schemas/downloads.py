from pydantic import BaseModel, ConfigDict


class DatasetDownloadJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    dataset_id: str | None = None
    dataset_key: str
    repo_id: str
    target_relative_path: str
    file_count: int | None = None
    downloaded_bytes: int | None = None
    overwrite: bool
