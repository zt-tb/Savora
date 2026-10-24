import asyncio
import types
import unittest
from datetime import timedelta
from unittest import mock

from tests import _stubs  # noqa: F401
from tests._fakes import FakeBot, FakeContext, FakeMessage, FakeUpdate, FakeUser

from app import monitor
from app.config import settings
from app.handlers import payments


def run(coro):
    return asyncio.run(coro)


class FakeSession:
    existing = None
    added = []

    def __call__(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def scalar(self, stmt):
        return FakeSession.existing

    def add(self, row):
        FakeSession.added.append(row)

    async def commit(self):
        pass


class PayBase(unittest.TestCase):
    def setUp(self):
        FakeSession.existing, FakeSession.added = None, []
        self.grant = mock.AsyncMock(return_value=True)
        for p in (
            mock.patch.object(payments, "Session", FakeSession()),
            mock.patch.object(payments, "lang_of", mock.AsyncMock(return_value="ar")),
            mock.patch.object(payments.users, "get_language", mock.AsyncMock(return_value="ar")),
            mock.patch.object(payments.users, "is_banned", mock.AsyncMock(return_value=False)),
            mock.patch.object(payments.users, "get_or_create", mock.AsyncMock()),
            mock.patch.object(payments.users, "grant_vip", self.grant),
            mock.patch.object(payments.users, "vip_remaining", mock.AsyncMock(return_value=timedelta(days=7))),
            mock.patch.object(payments.users, "revoke_vip", mock.AsyncMock(return_value=True)),
        ):
            p.start()
            self.addCleanup(p.stop)


class TestPayments(PayBase):
    def test_invoice_uses_stars_without_provider_token(self):
        ctx = FakeContext(FakeBot())
        run(payments.buy_plan(FakeUpdate(), ctx, "d7"))
        inv = ctx.bot.invoices[0]
        self.assertEqual(inv["currency"], "XTR")
        self.assertNotIn("provider_token", inv)
        self.assertEqual(inv["payload"], "vip:d7")
        self.assertEqual(len(inv["prices"]), 1)

    def test_unknown_plan_rejected(self):
        ctx = FakeContext(FakeBot())
        run(payments.buy_plan(FakeUpdate(), ctx, "d999"))
        self.assertEqual(ctx.bot.invoices, [])
        self.assertEqual(len(ctx.bot.sent), 1)

    def _pre(self, payload, currency="XTR"):
        answers = []

        async def answer(ok, error_message=None):
            answers.append((ok, error_message))
        q = types.SimpleNamespace(invoice_payload=payload, currency=currency, from_user=FakeUser(), answer=answer)
        upd = FakeUpdate()
        upd.pre_checkout_query = q
        run(payments.precheckout(upd, FakeContext()))
        return answers[0]

    def test_precheckout(self):
        self.assertEqual(self._pre("vip:d1")[0], True)
        self.assertEqual(self._pre("vip:zzz")[0], False)
        self.assertEqual(self._pre("vip:d1", "USD")[0], False)

    def _pay(self, payload="vip:d7", charge="ch1"):
        sp = types.SimpleNamespace(invoice_payload=payload, telegram_payment_charge_id=charge, total_amount=250)
        msg = FakeMessage()
        msg.successful_payment = sp
        ctx = FakeContext(FakeBot())
        run(payments.successful_payment(FakeUpdate(message=msg), ctx))
        return msg, ctx

    def test_successful_payment_grants_vip_once(self):
        msg, ctx = self._pay()
        self.grant.assert_awaited_once()
        self.assertEqual(self.grant.await_args.kwargs["hours"], 24 * 7)
        self.assertEqual(len(FakeSession.added), 1)
        self.assertEqual(len(msg.replies), 1)
        self.assertEqual(ctx.bot.sent[0][0], settings.admin_id)

    def test_duplicate_charge_is_ignored(self):
        FakeSession.existing = object()
        msg, ctx = self._pay()
        self.grant.assert_not_awaited()
        self.assertEqual(msg.replies, [])

    def test_unknown_payload_alerts_owner_without_grant(self):
        msg, ctx = self._pay(payload="evil")
        self.grant.assert_not_awaited()
        self.assertEqual(ctx.bot.sent[0][0], settings.admin_id)

    def test_grant_failure_alerts_owner(self):
        self.grant.return_value = False
        msg, ctx = self._pay()
        self.assertEqual(msg.replies, [])
        self.assertEqual(ctx.bot.sent[0][0], settings.admin_id)

    def test_refund_admin_only_and_usage(self):
        ctx = FakeContext(FakeBot(), args=["5", "ch9"])
        msg = FakeMessage()
        with mock.patch.object(payments, "is_admin", lambda u: False):
            run(payments.refund(FakeUpdate(message=msg), ctx))
        self.assertEqual((msg.replies, ctx.bot.refunds), ([], []))
        with mock.patch.object(payments, "is_admin", lambda u: True):
            run(payments.refund(FakeUpdate(message=msg), ctx))
            self.assertEqual(ctx.bot.refunds, [(5, "ch9")])
            bad = FakeMessage()
            run(payments.refund(FakeUpdate(message=bad), FakeContext(FakeBot(), args=["x"])))
            self.assertEqual(len(bad.replies), 1)
            ctx.bot.fail_refund = True
            fail = FakeMessage()
            run(payments.refund(FakeUpdate(message=fail), ctx))
            self.assertEqual(len(fail.replies), 1)


class TestMonitor(unittest.TestCase):
    def setUp(self):
        monitor.reset()
        self.addCleanup(monitor.reset)
        p = mock.patch.object(monitor.users, "get_language", mock.AsyncMock(return_value="ar"))
        p.start()
        self.addCleanup(p.stop)

    def check(self, status, bot):
        with mock.patch.object(monitor.telethon_runtime, "health", mock.AsyncMock(return_value=status)):
            return run(monitor.run_check(bot))

    def test_alert_once_then_recovery(self):
        bot = FakeBot()
        self.check("ok", bot)
        self.assertEqual(bot.sent, [])
        self.check("disconnected", bot)
        self.assertEqual(len(bot.sent), 1)
        self.check("disconnected", bot)
        self.assertEqual(len(bot.sent), 1)
        self.check("ok", bot)
        self.assertEqual(len(bot.sent), 2)

    def test_repeat_after_interval(self):
        bot = FakeBot()
        self.check("unauthorized", bot)
        monitor._state["alerted_at"] -= monitor.ALERT_REPEAT_SECONDS + 1
        self.check("unauthorized", bot)
        self.assertEqual(len(bot.sent), 2)

    def test_none_means_no_alert(self):
        bot = FakeBot()
        self.check("none", bot)
        self.assertEqual(bot.sent, [])

    def test_session_dead_cooldown(self):
        bot = FakeBot()
        run(monitor.report_session_dead(bot))
        run(monitor.report_session_dead(bot))
        self.assertEqual(len(bot.sent), 1)

    def test_health_job_swallows_errors(self):
        with mock.patch.object(monitor, "run_check", mock.AsyncMock(side_effect=RuntimeError("x"))):
            run(monitor.health_job(types.SimpleNamespace(bot=FakeBot())))


if __name__ == "__main__":
    unittest.main()
