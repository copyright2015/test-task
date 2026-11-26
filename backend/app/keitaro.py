from typing import Any

import httpx
from fastapi import HTTPException

from app.config import settings


class KeitaroClient:
    def __init__(self) -> None:
        self.base_url = settings.keitaro_base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        if not settings.keitaro_api_key:
            raise HTTPException(status_code=503, detail="KEITARO_API_KEY is not configured")
        return {"Api-Key": settings.keitaro_api_key}

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=20) as client:
                response = await client.request(method, path, headers=self._headers(), **kwargs)
                response.raise_for_status()
        except HTTPException:
            raise
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Keitaro API returned {exc.response.status_code}: {exc.response.text}",
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Could not reach Keitaro API: {exc}") from exc
        if response.status_code == 204 or not response.content:
            return None
        return response.json()


keitaro = KeitaroClient()


def collection_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "campaigns", "offers", "groups", "domains", "traffic_sources"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []
