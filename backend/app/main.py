import json
import asyncio
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.keitaro import collection_items, keitaro
from app.models import Campaign, Country, Offer, Stream, StreamOffer
from app.schemas import CampaignCreate, CampaignEditorUpdate

app = FastAPI(title="Campaign Manager API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def item_id(item: dict[str, Any]) -> str:
    value = item.get("id")
    if value is None:
        raise HTTPException(status_code=502, detail="Keitaro response item is missing its id")
    return str(value)


def has_active_offers(stream: dict[str, Any]) -> bool:
    offers = stream.get("offers", [])
    return isinstance(offers, list) and any(
        isinstance(offer, dict)
        and not offer.get("deleted")
        and offer.get("state", "active") == "active"
        for offer in offers
    )


def is_active_offer_stream(stream: dict[str, Any]) -> bool:
    return stream.get("state", "active") == "active" and has_active_offers(stream)


def save_campaign(db: Session, item: dict[str, Any]) -> Campaign:
    identifier = item_id(item)
    campaign = db.get(Campaign, identifier)
    if campaign is None:
        campaign = Campaign(id=identifier, name=str(item.get("name", identifier)))
        db.add(campaign)
    campaign.name = str(item.get("name", campaign.name))
    campaign.alias = item.get("alias")
    campaign.state = item.get("state")
    campaign.raw_json = json.dumps(item)
    return campaign


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/campaigns")
async def list_campaigns(
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if refresh:
        items = collection_items(await keitaro.request("GET", "/campaigns", params={"offset": 0, "limit": 100}))
        for item in items:
            save_campaign(db, item)
        db.commit()
    return [
        {"id": item.id, "name": item.name, "alias": item.alias, "state": item.state}
        for item in db.scalars(select(Campaign).order_by(Campaign.synced_at.desc())).all()
    ]


@app.get("/api/catalog")
async def catalog(db: Session = Depends(get_db)) -> dict[str, Any]:
    offers, groups, domains, sources = await asyncio.gather(
        keitaro.request("GET", "/offers"),
        keitaro.request("GET", "/groups", params={"type": "campaigns"}),
        keitaro.request("GET", "/domains"),
        keitaro.request("GET", "/traffic_sources"),
    )
    offer_items = collection_items(offers)
    for item in offer_items:
        identifier = item_id(item)
        offer = db.get(Offer, identifier)
        if offer is None:
            offer = Offer(id=identifier, name=str(item.get("name", identifier)))
            db.add(offer)
        offer.name = str(item.get("name", identifier))
        offer.state = item.get("state")
        offer.raw_json = json.dumps(item)
    db.commit()
    return {
        "geos": [{"code": item.code, "name": item.name} for item in db.scalars(select(Country).order_by(Country.name)).all()],
        "offers": offer_items,
        "groups": collection_items(groups),
        "domains": collection_items(domains),
        "traffic_sources": collection_items(sources),
    }


@app.post("/api/campaigns", status_code=201)
async def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    if db.get(Country, payload.geo_code) is None:
        raise HTTPException(status_code=422, detail="Selected country code is not available")
    catalog_data = await catalog(db)
    if not any(item_id(offer) == payload.offer_id for offer in catalog_data["offers"]):
        raise HTTPException(status_code=422, detail="Selected offer was not found")
    campaign_payload: dict[str, Any] = {"name": payload.name}
    for field, collection in (
        ("domain_id", "domains"),
        ("group_id", "groups"),
        ("traffic_source_id", "traffic_sources"),
    ):
        if not catalog_data[collection] or catalog_data[collection][0].get("id") is None:
            raise HTTPException(status_code=422, detail=f"Keitaro has no available {collection.replace('_', ' ')}")
        campaign_payload[field] = catalog_data[collection][0]["id"]
    campaign_data = await keitaro.request("POST", "/campaigns", json=campaign_payload)
    if not isinstance(campaign_data, dict):
        raise HTTPException(status_code=502, detail="Keitaro returned an invalid campaign response")
    campaign = save_campaign(db, campaign_data)
    db.commit()
    try:
        streams = [
            {
                "campaign_id": campaign.id,
                "name": "Country redirect",
                "position": 1,
                "type": "regular",
                "schema": "redirect",
                "filters": [{"name": "country", "mode": "accept", "payload": [payload.geo_code]}],
                "action_type": "http",
                "action_options": {"url": "https://www.google.com"},
                "offers": [],
            },
            {
                "campaign_id": campaign.id,
                "name": "Selected offer",
                "position": 2,
                "type": "regular",
                "schema": "landings",
                "filters": [],
                "action_type": "http",
                "offers": [{"offer_id": payload.offer_id, "share": 100, "state": "active"}],
            },
        ]
        for stream in streams:
            await keitaro.request("POST", "/streams", json=stream)
    except HTTPException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Campaign {campaign.id} was created, but stream setup failed: {exc.detail}",
        ) from exc
    return {"id": campaign.id, "name": campaign.name}


@app.get("/api/campaigns/{campaign_id}/editor")
async def campaign_editor(campaign_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    campaign, streams_payload = await asyncio.gather(
        keitaro.request("GET", f"/campaigns/{campaign_id}"),
        keitaro.request("GET", f"/campaigns/{campaign_id}/streams"),
    )
    items = collection_items(streams_payload)
    if not isinstance(campaign, dict):
        raise HTTPException(status_code=404, detail="Campaign was not found")
    save_campaign(db, campaign)
    for data in items:
        stream_id = item_id(data)
        stream = db.get(Stream, stream_id)
        if stream is None:
            stream = Stream(id=stream_id, campaign_id=campaign_id, name=str(data.get("name", stream_id)))
            db.add(stream)
        stream.campaign_id = campaign_id
        stream.name = str(data.get("name", stream_id))
        stream.position = int(data.get("position", 0))
        stream.raw_json = json.dumps(data)
        api_offers = data.get("offers", [])
        active_offer_ids: set[str] = set()
        if isinstance(api_offers, list):
            for offer_data in api_offers:
                if not isinstance(offer_data, dict):
                    continue
                offer_id_value = offer_data.get("offer_id") or offer_data.get("id")
                if offer_id_value is None:
                    continue
                offer_id = str(offer_id_value)
                active_offer_ids.add(offer_id)
                association = db.scalar(
                    select(StreamOffer).where(
                        StreamOffer.stream_id == stream_id,
                        StreamOffer.offer_id == offer_id,
                    )
                )
                if association is None:
                    association = StreamOffer(stream_id=stream_id, offer_id=offer_id)
                    db.add(association)
                    association.fixed = bool(offer_data.get("fixed", False))
                association.active = True
                association.weight = float(offer_data.get("share", offer_data.get("weight", 0)))
                if "fixed" in offer_data:
                    association.fixed = bool(offer_data["fixed"])
                offer_data.setdefault("fixed", association.fixed)
                association.raw_json = json.dumps(offer_data)
        archived = db.scalars(
            select(StreamOffer).where(StreamOffer.stream_id == stream_id, StreamOffer.active.is_(False))
        ).all()
        data["offers"] = list(api_offers) if isinstance(api_offers, list) else []
        data["offers"].extend(
            {
                **json.loads(item.raw_json),
                "offer_id": item.offer_id,
                "share": 0,
                "fixed": item.fixed,
                "deleted": True,
            }
            for item in archived
            if item.offer_id not in active_offer_ids
        )
    db.commit()
    return {"campaign": campaign, "streams": items}


@app.put("/api/campaigns/{campaign_id}/editor")
async def update_campaign_editor(
    campaign_id: str,
    payload: CampaignEditorUpdate,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    current = collection_items(await keitaro.request("GET", f"/campaigns/{campaign_id}/streams"))
    current_ids = {item_id(item) for item in current}
    submitted_ids = {str(item["id"]) for item in payload.streams if item.get("id") is not None}
    removed_ids = current_ids - submitted_ids
    if removed_ids:
        if any(not has_active_offers(item) for item in current if item_id(item) in removed_ids):
            raise HTTPException(status_code=422, detail="Streams without active offers cannot be deleted")
        active_ids = {item_id(item) for item in current if is_active_offer_stream(item)}
        remaining_active_ids = {
            str(item["id"])
            for item in payload.streams
            if item.get("id") is not None
            and str(item["id"]) in active_ids
            and is_active_offer_stream(item)
        }
        if len(active_ids) < 2 or not remaining_active_ids:
            raise HTTPException(status_code=422, detail="At least one saved active offer stream must remain")
    for stream in payload.streams:
        fixed_total = sum(
            float(offer.get("share", offer.get("weight", 0)))
            for offer in stream.get("offers", [])
            if isinstance(offer, dict) and offer.get("fixed") and not offer.get("deleted")
        )
        if fixed_total > 100:
            raise HTTPException(status_code=422, detail="Fixed offer shares cannot exceed 100%")
    for stream_id in removed_ids:
        await keitaro.request("DELETE", f"/streams/{stream_id}")
        db_stream = db.get(Stream, stream_id)
        if db_stream is not None:
            db.delete(db_stream)
    for position, stream in enumerate(payload.streams):
        submitted_offers = stream.get("offers", [])
        stream_data = {
            key: value
            for key, value in stream.items()
            if key not in {"id", "offers", "deleted", "fixed"}
        }
        stream_data["offers"] = [
            {
                "offer_id": offer.get("offer_id", offer.get("id")),
                "share": int(round(float(offer.get("share", offer.get("weight", 0))))),
                **({"state": offer["state"]} if "state" in offer else {}),
            }
            for offer in submitted_offers
            if isinstance(offer, dict) and not offer.get("deleted")
        ]
        stream_data["campaign_id"] = campaign_id
        stream_data["position"] = position
        if stream.get("id") is None:
            stream_data.setdefault("type", "regular")
            stream_data.setdefault("schema", "landings")
            stream_data.setdefault("action_type", "http")
            await keitaro.request("POST", "/streams", json=stream_data)
        else:
            stream_id = str(stream["id"])
            await keitaro.request("PUT", f"/streams/{stream_id}", json=stream_data)
            existing_associations = db.scalars(
                select(StreamOffer).where(StreamOffer.stream_id == stream_id)
            ).all()
            included_ids = {
                str(offer.get("offer_id", offer.get("id")))
                for offer in submitted_offers
                if isinstance(offer, dict)
            }
            for association in existing_associations:
                if association.offer_id not in included_ids:
                    association.active = False
                    association.weight = 0
            for offer in submitted_offers:
                if not isinstance(offer, dict):
                    continue
                offer_id_value = offer.get("offer_id", offer.get("id"))
                if offer_id_value is None:
                    continue
                offer_id = str(offer_id_value)
                association = next(
                    (item for item in existing_associations if item.offer_id == offer_id),
                    None,
                )
                if association is None:
                    association = StreamOffer(stream_id=stream_id, offer_id=offer_id)
                    db.add(association)
                    existing_associations.append(association)
                association.active = not bool(offer.get("deleted"))
                association.weight = 0 if offer.get("deleted") else float(
                    offer.get("share", offer.get("weight", 0))
                )
                association.fixed = bool(offer.get("fixed", False))
                association.raw_json = json.dumps(offer)
    db.commit()
    return {"status": "saved"}


@app.delete("/api/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    await keitaro.request("DELETE", f"/campaigns/{campaign_id}")
    campaign = db.get(Campaign, campaign_id)
    if campaign is not None:
        db.delete(campaign)
        db.commit()
    return {"status": "deleted"}


@app.post("/api/campaigns/{campaign_id}/{action}")
async def set_campaign_state(
    campaign_id: str,
    action: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if action not in {"enable", "disable"}:
        raise HTTPException(status_code=404, detail="Unsupported campaign action")
    await keitaro.request("POST", f"/campaigns/{campaign_id}/{action}")
    campaign = db.get(Campaign, campaign_id)
    if campaign is not None:
        campaign.state = "active" if action == "enable" else "disabled"
        db.commit()
    return {"status": action}
