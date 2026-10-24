from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import select
from telegram import InlineKeyboardMarkup, LabeledPrice, Update
from telegram.ext import ContextTypes

from .. import emoji_ids as E
from .. import users
from ..buttons import PRIMARY, SUCCESS, btn, url_btn
from ..config import settings
from ..db import Session
from ..models import Payment
from ..plans import PLAN_HOURS, per_day_stars, plan_stars
from ..texts import text
from ..ui import esc, human_delta
from .common import back_keyboard, edit_menu, is_admin, lang_of

logger = logging.getLogger(__name__)

BUY_PREFIX = "buy_vip_"
PAYLOAD_PREFIX = "vip:"
async def show_vip_sub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    language = await lang_of(update)
    body = text(language, "vip_price", d1=plan_stars("d1"), d7=plan_stars("d7"), d30=plan_stars("d30"),
                vip_batch=users.VIP_BATCH_LIMIT, per_day=per_day_stars())
    plans_row = [btn(text(language, "buy_btn", stars=plan_stars(plan), plan=text(language, f"plan_{plan}")),
                     f"{BUY_PREFIX}{plan}", style=SUCCESS, emoji=E.MEDAL) for plan in PLAN_HOURS]
    footer_row = [url_btn(text(language, "contact_btn"), "https://t.me/K0_MG", style=PRIMARY, emoji=E.MAIL),
                  *back_keyboard(language).inline_keyboard[0]]
    await edit_menu(update, body, reply_markup=InlineKeyboardMarkup([plans_row, footer_row]))


async def buy_plan(update: Update, context: ContextTypes.DEFAULT_TYPE, plan: str) -> None:
    language = await lang_of(update)
    if plan not in PLAN_HOURS or await users.is_banned(update.effective_user.id):
        await context.bot.send_message(update.effective_chat.id, text(language, "pay_rejected"))
        return
    plan_label = text(language, f"plan_{plan}")
    await context.bot.send_invoice(
        chat_id=update.effective_chat.id,
        title=text(language, "invoice_title", plan=plan_label),
        description=text(language, "invoice_desc", plan=plan_label),
        payload=f"{PAYLOAD_PREFIX}{plan}",
        currency="XTR",
        prices=[LabeledPrice(text(language, "invoice_title", plan=plan_label), plan_stars(plan))],
    )


def _plan_from_payload(payload: str) -> str | None:
    if payload.startswith(PAYLOAD_PREFIX):
        plan = payload[len(PAYLOAD_PREFIX):]
        if plan in PLAN_HOURS:
            return plan
    return None


async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    plan = _plan_from_payload(query.invoice_payload or "")
    language = await users.get_language(query.from_user.id)
    if plan is None or query.currency != "XTR" or await users.is_banned(query.from_user.id):
        await query.answer(ok=False, error_message=text(language, "pay_rejected"))
        return
    await query.answer(ok=True)


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    payment = message.successful_payment
    user = update.effective_user
    plan = _plan_from_payload(payment.invoice_payload or "")
    charge = payment.telegram_payment_charge_id
    language = await lang_of(update)
    owner_language = await users.get_language(settings.admin_id)

    async with Session() as s:
        already = await s.scalar(select(Payment).where(Payment.charge_id == charge))
    if already is not None:
        return
    if plan is None:
        logger.error("دفعة بحمولة غير معروفة: %r (charge=%s)", payment.invoice_payload, charge)
        await context.bot.send_message(settings.admin_id, text(
            owner_language, "pay_grant_failed", user_id=user.id, plan=esc(payment.invoice_payload), charge=esc(charge)))
        return

    hours = PLAN_HOURS[plan]
    async with Session() as s:
        s.add(Payment(user_id=user.id, charge_id=charge, plan=plan, stars=payment.total_amount, hours=hours))
        await s.commit()
    await users.get_or_create(user.id, user.full_name or str(user.id), user.username)
    if not await users.grant_vip(user.id, hours=hours):
        logger.error("فشل تفعيل VIP بعد دفعة ناجحة (user=%s charge=%s)", user.id, charge)
        await context.bot.send_message(settings.admin_id, text(
            owner_language, "pay_grant_failed", user_id=user.id, plan=plan, charge=esc(charge)))
        return

    remaining = await users.vip_remaining(user.id) or timedelta(hours=hours)
    await message.reply_text(text(language, "pay_success", plan=text(language, f"plan_{plan}"),
                                  remaining=human_delta(remaining, language)))
    try:
        await context.bot.send_message(settings.admin_id, text(
            owner_language, "pay_admin_note", user_id=user.id, name=esc(user.full_name),
            plan=text(owner_language, f"plan_{plan}"), stars=payment.total_amount, charge=esc(charge)))
    except Exception:
        logger.warning("تعذّر إبلاغ المالك بالدفعة", exc_info=True)


async def paysupport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    language = await lang_of(update)
    await update.message.reply_text(text(language, "paysupport_text"))


async def terms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    language = await lang_of(update)
    await update.message.reply_text(text(language, "terms_text"))


async def refund(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    args = context.args or []
    if len(args) != 2 or not args[0].lstrip("-").isdigit():
        await update.message.reply_text(text(language, "refund_usage"))
        return
    target, charge = int(args[0]), args[1]
    try:
        await context.bot.refund_star_payment(user_id=target, telegram_payment_charge_id=charge)
    except Exception as exc:
        await update.message.reply_text(text(language, "refund_failed", esc(exc)))
        return
    await users.revoke_vip(target)
    await update.message.reply_text(text(language, "refund_done", target))
