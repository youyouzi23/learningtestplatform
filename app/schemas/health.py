from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health-check response body."""

    status: Literal["ok"]
    service: str
    version: str

