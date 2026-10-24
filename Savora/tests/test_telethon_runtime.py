import asyncio
import unittest

from tests import _stubs  # noqa: F401

from app import telethon_runtime as tr


def run(coro):
    return asyncio.run(coro)


class FakeClient:
    def __init__(self, authorized=True, name="Ali", fail_connect=False):
        self.authorized = authorized
        self.name = name
        self.fail_connect = fail_connect
        self.connected = False
        self.disconnected_called = False

    async def connect(self):
        if self.fail_connect:
            raise ConnectionError("لا يمكن الاتصال")
        self.connected = True

    async def disconnect(self):
        self.connected = False
        self.disconnected_called = True

    async def is_user_authorized(self):
        return self.authorized

    async def get_me(self):
        class _Me:
            first_name = self.name
            id = 42
        return _Me()


class TestShutdownRegression(unittest.TestCase):

    def setUp(self):
        tr._client = None

    def test_shutdown_with_no_active_client_does_not_raise(self):
        run(tr.shutdown())
        self.assertIsNone(run(tr.get_client()))

    def test_shutdown_disconnects_active_client_and_clears_it(self):
        fake = FakeClient()
        tr._client = fake
        run(tr.shutdown())
        self.assertTrue(fake.disconnected_called)
        self.assertIsNone(run(tr.get_client()))

    def test_shutdown_is_safe_to_call_twice(self):
        tr._client = FakeClient()
        run(tr.shutdown())
        run(tr.shutdown())


class TestSwap(unittest.TestCase):

    def setUp(self):
        tr._client = None
        self._orig_new_client = tr._new_client

    def tearDown(self):
        tr._new_client = self._orig_new_client

    def _use_fake(self, fake_client):
        tr._new_client = lambda session_string: fake_client

    def test_swap_success_replaces_client(self):
        old = FakeClient(name="Old")
        tr._client = old
        new = FakeClient(name="New")
        self._use_fake(new)
        ok, info = run(tr.swap("some-session-string"))
        self.assertTrue(ok)
        self.assertEqual(info, "New")
        self.assertTrue(old.disconnected_called)
        self.assertIs(run(tr.get_client()), new)

    def test_swap_rejects_unauthorized_session(self):
        tr._client = None
        self._use_fake(FakeClient(authorized=False))
        ok, info = run(tr.swap("some-session-string"))
        self.assertFalse(ok)
        self.assertIsNone(run(tr.get_client()))

    def test_swap_rejects_connection_failure(self):
        tr._client = None
        self._use_fake(FakeClient(fail_connect=True))
        ok, info = run(tr.swap("some-session-string"))
        self.assertFalse(ok)
        self.assertIsNone(run(tr.get_client()))

    def test_swap_failure_keeps_old_client_running(self):
        old = FakeClient(name="StillHere")
        tr._client = old
        self._use_fake(FakeClient(authorized=False))
        ok, _ = run(tr.swap("some-session-string"))
        self.assertFalse(ok)
        self.assertIs(run(tr.get_client()), old)
        self.assertFalse(old.disconnected_called)


if __name__ == "__main__":
    unittest.main()
