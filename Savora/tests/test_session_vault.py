import asyncio
import unittest

from tests import _stubs  # noqa: F401

from app import session_vault as sv


def run(coro):
    return asyncio.run(coro)


class TestSealUnseal(unittest.TestCase):
    def test_roundtrip(self):
        blob = sv.seal("1ApWgASNmEU-very-secret-string")
        self.assertNotIn("very-secret-string", blob)
        self.assertEqual(sv.unseal(blob), "1ApWgASNmEU-very-secret-string")

    def test_tampered_blob_raises_vault_decrypt_error(self):
        blob = sv.seal("secret")
        tampered = blob[:-4] + "xxxx"
        with self.assertRaises(sv.VaultDecryptError):
            sv.unseal(tampered)

    def test_different_calls_produce_different_ciphertext(self):
        b1 = sv.seal("same-secret")
        b2 = sv.seal("same-secret")
        self.assertNotEqual(b1, b2)


class FakeRow:
    def __init__(self, id, blob):
        self.id = id
        self.blob = blob


class FakeDbSessionCM:

    table: dict[int, FakeRow] = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, model, pk):
        return self.table.get(pk)

    def add(self, obj):
        self.table[obj.id] = obj

    async def delete(self, obj):
        self.table.pop(obj.id, None)

    async def commit(self):
        pass


class TestCandidateAndPersistence(unittest.TestCase):
    def setUp(self):
        FakeDbSessionCM.table = {}
        sv.redis.store.clear()
        self._orig_dbsession = sv.DbSession
        sv.DbSession = FakeDbSessionCM

    def tearDown(self):
        sv.DbSession = self._orig_dbsession

    def test_candidate_round_trip(self):
        run(sv.put_candidate("string-session-abc", {"id": 1, "name": "Test"}))
        session_string, meta = run(sv.take_candidate())
        self.assertEqual(session_string, "string-session-abc")
        self.assertEqual(meta["name"], "Test")

    def test_candidate_is_consumed_once(self):
        run(sv.put_candidate("x", {}))
        self.assertIsNotNone(run(sv.take_candidate()))
        self.assertIsNone(run(sv.take_candidate()))

    def test_no_candidate_returns_none(self):
        self.assertIsNone(run(sv.take_candidate()))

    def test_drop_candidate(self):
        run(sv.put_candidate("y", {}))
        run(sv.drop_candidate())
        self.assertIsNone(run(sv.take_candidate()))

    def test_save_then_load_roundtrip(self):
        run(sv.save_session("final-session-string"))
        loaded = run(sv.load_session())
        self.assertEqual(loaded, "final-session-string")

    def test_load_without_any_saved_session_returns_none(self):
        self.assertIsNone(run(sv.load_session()))

    def test_load_falls_back_to_postgres_when_redis_cache_empty(self):
        run(sv.save_session("db-backed-session"))
        sv.redis.store.pop(sv.CACHE_KEY, None)
        self.assertEqual(run(sv.load_session()), "db-backed-session")

    def test_clear_session_removes_both_db_and_cache(self):
        run(sv.save_session("to-delete"))
        run(sv.clear_session())
        self.assertIsNone(run(sv.load_session()))

    def test_overwriting_save_replaces_previous_session(self):
        run(sv.save_session("old"))
        run(sv.save_session("new"))
        self.assertEqual(run(sv.load_session()), "new")


if __name__ == "__main__":
    unittest.main()
