from typing import Any

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1)
    geo_code: str
    offer_id: str


class CampaignSummary(BaseModel):
    id: str
    name: str
    alias: str | None = None
    state: str | None = None


class CampaignEditorUpdate(BaseModel):
    streams: list[dict[str, Any]]
