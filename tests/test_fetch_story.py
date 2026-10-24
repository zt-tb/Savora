import asyncio
import unittest

from tests import _stubs  # noqa: F401

from app import downloader as dl
from telethon.errors import FloodWaitError, StoryIdEmptyError  # noqa: E402
from telethon.tl.functions.stories import GetStoriesByIDRequest  # noqa: E402


def run(coro):
    return asyncio.run(coro)


class FakeStoryItem:
    def __init__(self, media=None, caption=""):
        self.media = media
        self.caption = caption


class FakeStoriesResult:
    def __init__(self, stories):
        self.stories = stories


class FakeResolvedEntity:

    def __init__(self, source):
        self.source = source


class FakeClientForStories:

    def __init__(self, response=None, raise_exc=None, entity_raise_exc=None):
        self.response = response
        self.raise_exc = raise_exc
        self.entity_raise_exc = entity_raise_exc
        self.last_request = None
        self.get_entity_called_with = None

    async def get_entity(self, chat):
        self.get_entity_called_with = chat
        if self.entity_raise_exc is not None:
            raise self.entity_raise_exc
        return FakeResolvedEntity(chat)

    async def __call__(self, request):
        self.last_request = request
        if self.raise_exc is not None:
            raise self.raise_exc
        return self.response

    async def get_messages(self, chat, ids=None):
        raise AssertionError("fetch_story ما لازم يستدعي get_messages إطلاقاً — API مختلف كلياً")


class TestFetchStoryUsesCorrectAPI(unittest.TestCase):
    def test_fetch_story_calls_get_stories_by_id_not_get_messages(self):
        item = FakeStoryItem(media=object(), caption="قصة تجريبية")
        client = FakeClientForStories(response=FakeStoriesResult([item]))
        result = run(dl.fetch_story(client, "somechannel", 11))
        self.assertIs(result, item)
        self.assertIsInstance(client.last_request, GetStoriesByIDRequest)
        self.assertEqual(client.get_entity_called_with, "somechannel")
        self.assertIsInstance(client.last_request.peer, FakeResolvedEntity)
        self.assertEqual(client.last_request.peer.source, "somechannel")
        self.assertEqual(client.last_request.id, [11])

    def test_fetch_story_resolves_entity_before_raw_request(self):
        item = FakeStoryItem(media=object())
        client = FakeClientForStories(response=FakeStoriesResult([item]))
        run(dl.fetch_story(client, "another_channel", 5))
        self.assertEqual(client.get_entity_called_with, "another_channel")
        self.assertNotEqual(client.last_request.peer, "another_channel")

    def test_fetch_story_translates_unresolved_entity_to_private_access(self):
        client = FakeClientForStories(entity_raise_exc=ValueError("Cannot find entity"))
        with self.assertRaises(dl.DownloadError) as ctx:
            run(dl.fetch_story(client, "unknown_channel", 11))
        self.assertEqual(ctx.exception.code, "private_access")

    def test_fetch_story_raises_story_unavailable_when_empty(self):
        client = FakeClientForStories(response=FakeStoriesResult([]))
        with self.assertRaises(dl.DownloadError) as ctx:
            run(dl.fetch_story(client, "somechannel", 999))
        self.assertEqual(ctx.exception.code, "story_unavailable")

    def test_fetch_story_translates_rpc_error_to_story_unavailable(self):
        client = FakeClientForStories(raise_exc=StoryIdEmptyError("expired"))
        with self.assertRaises(dl.DownloadError) as ctx:
            run(dl.fetch_story(client, "somechannel", 11))
        self.assertEqual(ctx.exception.code, "story_unavailable")

    def test_fetch_story_surfaces_flood_wait_with_seconds(self):
        client = FakeClientForStories(raise_exc=FloodWaitError(seconds=42))
        with self.assertRaises(dl.DownloadError) as ctx:
            run(dl.fetch_story(client, "somechannel", 11))
        self.assertEqual(ctx.exception.code, "flood_wait")
        self.assertEqual(ctx.exception.extra, "42")

    def test_media_kind_works_on_story_item_same_as_message(self):
        class FakeMedia:
            photo = object()
        item = FakeStoryItem(media=FakeMedia())
        self.assertEqual(dl.media_kind(item), "photo")


if __name__ == "__main__":
    unittest.main()
