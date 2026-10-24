import asyncio
import unittest

from tests import _stubs  # noqa: F401

from app.login_flow import LoginError, LoginSession, NeedsPassword
from telethon.errors import (  # noqa: E402
    PasswordHashInvalidError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    SessionPasswordNeededError,
)


def run(coro):
    return asyncio.run(coro)


class FakeSession:
    def __init__(self):
        self.saved = "FAKE-STRING-SESSION"

    def save(self):
        return self.saved


class FakeMe:
    def __init__(self, id=111, first_name="Ali", last_name=None, username="ali_t", phone="9647711112222"):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.phone = phone


class FakeQrLogin:
    def __init__(self, outcomes):
        self.url = "tg://login?token=abc"
        self._outcomes = list(outcomes)
        self.recreated = 0

    async def wait(self, timeout=None):
        outcome = self._outcomes.pop(0)
        if outcome == "expired":
            raise asyncio.TimeoutError
        if isinstance(outcome, type) and issubclass(outcome, Exception):
            raise outcome
        return True

    async def recreate(self):
        self.recreated += 1


class FakeClient:

    def __init__(self, phone_invalid=False, code_invalid=False, needs_password=False,
                 password_invalid=False, qr_outcomes=None):
        self.connected = False
        self.phone_invalid = phone_invalid
        self.code_invalid = code_invalid
        self.needs_password = needs_password
        self.password_invalid = password_invalid
        self.qr_outcomes = qr_outcomes or ["ok"]
        self.session = FakeSession()
        self._signed_in = False

    async def connect(self):
        self.connected = True

    async def disconnect(self):
        self.connected = False

    async def send_code_request(self, phone):
        if self.phone_invalid:
            raise PhoneNumberInvalidError("invalid")

        class _Sent:
            phone_code_hash = "hash123"
        return _Sent()

    async def sign_in(self, phone=None, code=None, phone_code_hash=None, password=None):
        if password is not None:
            if self.password_invalid:
                raise PasswordHashInvalidError("bad password")
            self._signed_in = True
            return
        if self.code_invalid:
            raise PhoneCodeInvalidError("bad code")
        if self.needs_password:
            raise SessionPasswordNeededError("need password")
        self._signed_in = True

    async def get_me(self):
        return FakeMe()

    async def qr_login(self):
        return FakeQrLogin(self.qr_outcomes)


class TestPhoneLoginHappyPath(unittest.TestCase):
    def setUp(self):
        from app.db import redis
        redis.store.clear()

    def test_full_phone_flow_succeeds_and_creates_candidate(self):
        calls = {}

        async def fake_put_candidate(session_string, meta):
            calls["session_string"] = session_string
            calls["meta"] = meta

        import app.session_vault as sv
        orig = sv.put_candidate
        sv.put_candidate = fake_put_candidate
        try:
            client = FakeClient()
            session = LoginSession(make_client=lambda: client)
            run(session.begin_phone("+9647711112222"))
            result = run(session.submit_code("12345"))
            self.assertEqual(result, "ok")
            meta = run(session.finish())
            self.assertEqual(meta["id"], 111)
            self.assertEqual(meta["name"], "Ali")
            self.assertEqual(meta["username"], "ali_t")
            self.assertEqual(calls["session_string"], "FAKE-STRING-SESSION")
            self.assertIsNone(session.client)
        finally:
            sv.put_candidate = orig

    def test_invalid_phone_raises_login_error_no_crash(self):
        client = FakeClient(phone_invalid=True)
        session = LoginSession(make_client=lambda: client)
        with self.assertRaises(LoginError):
            run(session.begin_phone("+123"))

    def test_invalid_code_raises_login_error(self):
        client = FakeClient(code_invalid=True)
        session = LoginSession(make_client=lambda: client)
        run(session.begin_phone("+9647711112222"))
        with self.assertRaises(LoginError):
            run(session.submit_code("00000"))

    def test_2fa_flow_needs_password_then_succeeds(self):
        client = FakeClient(needs_password=True)
        session = LoginSession(make_client=lambda: client)
        run(session.begin_phone("+9647711112222"))
        with self.assertRaises(NeedsPassword):
            run(session.submit_code("12345"))
        result = run(session.submit_password("secret-pass"))
        self.assertEqual(result, "ok")

    def test_wrong_password_raises_login_error(self):
        client = FakeClient(needs_password=True, password_invalid=True)
        session = LoginSession(make_client=lambda: client)
        run(session.begin_phone("+9647711112222"))
        with self.assertRaises(NeedsPassword):
            run(session.submit_code("12345"))
        with self.assertRaises(LoginError):
            run(session.submit_password("wrong"))

    def test_submit_code_without_begin_phone_raises(self):
        session = LoginSession(make_client=lambda: FakeClient())
        with self.assertRaises(LoginError):
            run(session.submit_code("12345"))

    def test_code_digits_are_extracted_from_spaced_input(self):
        client = FakeClient()
        session = LoginSession(make_client=lambda: client)
        run(session.begin_phone("+9647711112222"))
        result = run(session.submit_code("1 2 3 4 5"))
        self.assertEqual(result, "ok")

    def test_empty_code_raises_login_error(self):
        client = FakeClient()
        session = LoginSession(make_client=lambda: client)
        run(session.begin_phone("+9647711112222"))
        with self.assertRaises(LoginError):
            run(session.submit_code("   "))


class TestPhoneLoginRateLimits(unittest.TestCase):

    def setUp(self):
        from app.db import redis
        redis.store.clear()

    def test_phone_and_qr_have_independent_counters(self):
        from app.login_flow import MAX_PHONE_TRIES

        phone_session = LoginSession(make_client=lambda: FakeClient())
        for _ in range(MAX_PHONE_TRIES):
            run(phone_session.begin_phone("+9647711112222"))
        with self.assertRaises(LoginError):
            run(phone_session.begin_phone("+9647711112222"))

        qr_session = LoginSession(make_client=lambda: FakeClient(qr_outcomes=["ok"]))
        url = run(qr_session.begin_qr())
        self.assertTrue(url.startswith("tg://"))

    def test_many_phone_attempts_eventually_blocked_with_clear_message(self):
        from app.login_flow import MAX_PHONE_TRIES

        session = LoginSession(make_client=lambda: FakeClient())
        for _ in range(MAX_PHONE_TRIES):
            run(session.begin_phone("+9647711112222"))
        with self.assertRaises(LoginError) as ctx:
            run(session.begin_phone("+9647711112222"))
        self.assertIn("دقيقة", str(ctx.exception))

    def test_many_failed_codes_eventually_blocked(self):
        from app.login_flow import MAX_FAILS

        client = FakeClient(code_invalid=True)
        session = LoginSession(make_client=lambda: client)
        run(session.begin_phone("+9647711112222"))
        for _ in range(MAX_FAILS):
            with self.assertRaises(LoginError):
                run(session.submit_code("00000"))
        with self.assertRaises(LoginError):
            run(session.submit_code("00000"))

    def test_clear_rate_limits_resets_all_counters(self):
        from app.login_flow import MAX_PHONE_TRIES, clear_rate_limits

        session = LoginSession(make_client=lambda: FakeClient())
        for _ in range(MAX_PHONE_TRIES):
            run(session.begin_phone("+9647711112222"))
        with self.assertRaises(LoginError):
            run(session.begin_phone("+9647711112222"))

        run(clear_rate_limits())

        run(session.begin_phone("+9647711112222"))


class TestQrLogin(unittest.TestCase):
    def setUp(self):
        from app.db import redis
        redis.store.clear()

    def test_qr_begin_returns_url(self):
        client = FakeClient(qr_outcomes=["ok"])
        session = LoginSession(make_client=lambda: client)
        url = run(session.begin_qr())
        self.assertTrue(url.startswith("tg://"))

    def test_qr_wait_ok(self):
        client = FakeClient(qr_outcomes=["ok"])
        session = LoginSession(make_client=lambda: client)
        run(session.begin_qr())
        self.assertEqual(run(session.wait_qr()), "ok")

    def test_qr_wait_expired(self):
        client = FakeClient(qr_outcomes=["expired"])
        session = LoginSession(make_client=lambda: client)
        run(session.begin_qr())
        self.assertEqual(run(session.wait_qr()), "expired")

    def test_qr_wait_needs_password(self):
        client = FakeClient(qr_outcomes=[SessionPasswordNeededError])
        session = LoginSession(make_client=lambda: client)
        run(session.begin_qr())
        self.assertEqual(run(session.wait_qr()), "need_password")

    def test_qr_refresh_calls_recreate(self):
        client = FakeClient(qr_outcomes=["expired", "ok"])
        session = LoginSession(make_client=lambda: client)
        run(session.begin_qr())
        run(session.wait_qr())
        run(session.refresh_qr())
        self.assertEqual(session.qr.recreated, 1)

    def test_wait_qr_without_begin_raises(self):
        session = LoginSession(make_client=lambda: FakeClient())
        with self.assertRaises(LoginError):
            run(session.wait_qr())


class TestCancel(unittest.TestCase):
    def setUp(self):
        from app.db import redis
        redis.store.clear()

    def test_cancel_disconnects_and_clears_state(self):
        client = FakeClient()
        session = LoginSession(make_client=lambda: client)
        run(session.begin_phone("+9647711112222"))
        self.assertTrue(client.connected)
        run(session.cancel())
        self.assertFalse(client.connected)
        self.assertIsNone(session.client)
        self.assertIsNone(session.phone)

    def test_cancel_when_nothing_in_progress_is_safe(self):
        session = LoginSession(make_client=lambda: FakeClient())
        run(session.cancel())


if __name__ == "__main__":
    unittest.main()
