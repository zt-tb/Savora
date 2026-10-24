import asyncio
import unittest

from tests import _stubs  # noqa: F401

from app.handlers import session_login


def run(coro):
    return asyncio.run(coro)


class FakeMessage:
    def __init__(self, photo):
        self.photo = photo


class FakeQuery:
    def __init__(self, photo):
        self.message = FakeMessage(photo)
        self.caption_calls = []
        self.text_calls = []

    async def edit_message_caption(self, caption=None):
        self.caption_calls.append(caption)

    async def edit_message_text(self, body):
        self.text_calls.append(body)


class FakeUser:
    id = 7249021797


class FakeUpdate:
    def __init__(self, photo):
        self.callback_query = FakeQuery(photo)
        self.effective_user = FakeUser()


class TestActivateCandidateRespectsMessageType(unittest.TestCase):
    def setUp(self):
        from app.db import redis
        redis.store.clear()

    def test_no_candidate_on_photo_message_edits_caption_not_text(self):
        update = FakeUpdate(photo=[object()])
        run(session_login.activate_candidate(update, None))
        self.assertEqual(len(update.callback_query.caption_calls), 1)
        self.assertEqual(len(update.callback_query.text_calls), 0)
        self.assertIn("ما فيه حساب", update.callback_query.caption_calls[0])

    def test_no_candidate_on_text_message_edits_text_not_caption(self):
        update = FakeUpdate(photo=None)
        run(session_login.activate_candidate(update, None))
        self.assertEqual(len(update.callback_query.text_calls), 1)
        self.assertEqual(len(update.callback_query.caption_calls), 0)

    def test_successful_activation_on_photo_message_edits_caption(self):
        import app.session_vault as sv
        import app.telethon_runtime as tr

        orig_take = sv.take_candidate
        orig_swap = tr.swap
        orig_save = sv.save_session

        async def fake_take():
            return "fake-session-string", {"id": 1, "name": "Golden Band"}

        async def fake_swap(session_string):
            return True, "Golden Band"

        async def fake_save(session_string):
            pass

        sv.take_candidate = fake_take
        tr.swap = fake_swap
        sv.save_session = fake_save
        try:
            update = FakeUpdate(photo=[object()])
            run(session_login.activate_candidate(update, None))
            self.assertEqual(len(update.callback_query.caption_calls), 1)
            self.assertEqual(len(update.callback_query.text_calls), 0)
            self.assertIn("Golden Band", update.callback_query.caption_calls[0])
        finally:
            sv.take_candidate = orig_take
            tr.swap = orig_swap
            sv.save_session = orig_save

    def test_cancel_login_on_photo_message_edits_caption(self):
        update = FakeUpdate(photo=[object()])
        run(session_login.cancel_login(update, _FakeContext()))
        self.assertEqual(len(update.callback_query.caption_calls), 1)
        self.assertEqual(len(update.callback_query.text_calls), 0)


class _FakeContext:
    user_data: dict = {}

    def __init__(self):
        self.user_data = {}


if __name__ == "__main__":
    unittest.main()
