import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.main import keitaro, update_campaign_editor
from app.schemas import CampaignEditorUpdate


def stream(identifier: int, offers: bool = True, state: str = "active") -> dict:
    return {
        "id": identifier,
        "campaign_id": 1,
        "name": f"Stream {identifier}",
        "state": state,
        "offers": [{"offer_id": identifier, "share": 100}] if offers else [],
    }


class StreamDeletionTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    async def update(self, current: list[dict], submitted: list[dict]) -> AsyncMock:
        request = AsyncMock(side_effect=[current] + [{}] * 10)
        with patch.object(keitaro, "request", request):
            await update_campaign_editor("1", CampaignEditorUpdate(streams=submitted), self.db)
        return request

    async def test_cannot_delete_stream_without_offers(self) -> None:
        current = [stream(1, offers=False), stream(2), stream(3)]
        request = AsyncMock(return_value=current)
        with patch.object(keitaro, "request", request), self.assertRaises(HTTPException) as error:
            await update_campaign_editor("1", CampaignEditorUpdate(streams=current[1:]), self.db)
        self.assertEqual(error.exception.status_code, 422)
        request.assert_awaited_once_with("GET", "/campaigns/1/streams")

    async def test_cannot_delete_last_active_offer_stream(self) -> None:
        current = [stream(1), stream(2, state="disabled")]
        with self.assertRaises(HTTPException) as error:
            await self.update(current, [current[1]])
        self.assertEqual(error.exception.status_code, 422)

    async def test_disabled_offers_do_not_make_stream_deletable(self) -> None:
        inactive_offers = stream(1)
        inactive_offers["offers"][0]["state"] = "disabled"
        current = [inactive_offers, stream(2), stream(3)]
        with self.assertRaises(HTTPException) as error:
            await self.update(current, current[1:])
        self.assertEqual(error.exception.status_code, 422)

    async def test_can_delete_one_of_two_active_offer_streams(self) -> None:
        current = [stream(1), stream(2)]
        request = await self.update(current, [current[1]])
        request.assert_any_await("DELETE", "/streams/1")

    async def test_cannot_remove_both_or_remove_offers_from_survivor(self) -> None:
        current = [stream(1), stream(2)]
        for submitted in ([], [stream(2, offers=False)]):
            with self.subTest(submitted=submitted):
                with self.assertRaises(HTTPException) as error:
                    await self.update(current, submitted)
                self.assertEqual(error.exception.status_code, 422)

    async def test_unsaved_stream_cannot_replace_last_saved_offer_stream(self) -> None:
        current = [stream(1)]
        new_stream = {"name": "New", "offers": [{"offer_id": 2, "share": 100}]}
        with self.assertRaises(HTTPException) as error:
            await self.update(current, [new_stream])
        self.assertEqual(error.exception.status_code, 422)

    async def test_unchanged_stream_without_offers_can_still_be_saved(self) -> None:
        current = [stream(1, offers=False), stream(2)]
        request = await self.update(current, current)
        self.assertFalse(any(call.args[0] == "DELETE" for call in request.await_args_list))
