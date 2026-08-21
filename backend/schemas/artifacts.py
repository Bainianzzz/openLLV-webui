from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    kind: Literal["image", "output", "checkpoint", "dataset"]
    path_type: Literal["file", "directory"]
    display_name: str | None = None
    created_at: datetime
    content_url: str
