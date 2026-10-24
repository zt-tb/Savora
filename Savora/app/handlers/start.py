from __future__ import annotations

import logging

from sqlalchemy import select
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from .. import emoji_ids as E
from .. import users
from ..buttons import DANGER, SUCCESS, btn
from ..config import settings
from ..db import Session
from ..models import ShareRequest, ShareRequestStatus
from ..texts import text
from ..ui import esc, human_delta
from ..welcome_media import send_welcome
from .common import (back_keyboard, clear_state, edit_menu, get_state, is_admin, lang_of, language_keyboard,
                     main_keyboard, quota_view, set_state, upgrade_keyboard)

logger = logging.getLogger(__name__)

ST_SHARE_SCREENSHOT = "share_screenshot"


async def _upsert_user(update: Update) -> None:
    u = update.effective_user
    if u:
        await users.get_or_create(u.id, u.full_name or str(u.id), u.username)


async def _welcome(update: Update, language: str) -> tuple[str, InlineKeyboardMarkup]:
    u = update.effective_user
    vip = await users.is_vip(u.id)
    quota, nudge = await quota_view(u.id, language)
    body = text(language, "welcome", name=esc(u.first_name or u.full_name or u.id),
                plan=text(language, "plan_vip" if vip else "plan_free"), quota=quota, nudge=nudge)
    return body, main_keyboard(language, show_admin=is_admin(update), vip=vip)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _upsert_user(update)
    if await users.is_banned(update.effective_user.id):
        language = await lang_of(update)
        await update.message.reply_text(text(language, "you_are_banned"))
        return
    clear_state(context)
    language = await lang_of(update)
    body, markup = await _welcome(update, language)
    await send_welcome(update.message, body, markup)


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    clear_state(context)
    language = await lang_of(update)
    body, markup = await _welcome(update, language)
    await edit_menu(update, body, reply_markup=markup)


async def ask_download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    language = await lang_of(update)
    await edit_menu(update, text(language, "send_link"), reply_markup=back_keyboard(language))


async def show_language_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    language = await lang_of(update)
    await edit_menu(update, text(language, "select_language"), reply_markup=language_keyboard())


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE, language_code: str) -> None:
    await users.set_language(update.effective_user.id, language_code)
    body, markup = await _welcome(update, language_code)
    await edit_menu(update, f"{text(language_code, 'language_changed')}\n\n{body}", reply_markup=markup)


async def show_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    language = await lang_of(update)
    u = update.effective_user
    body = (text(language, "my_id_info", u.id, esc(u.username)) if u.username
            else text(language, "my_id_no_username", u.id))
    await edit_menu(update, body, reply_markup=back_keyboard(language))


async def show_vip_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    language = await lang_of(update)
    user_id = update.effective_user.id
    remaining = await users.vip_remaining(user_id)
    if remaining is not None:
        body, markup = text(language, "vip_active_status", remaining=human_delta(remaining, language)), back_keyboard(language)
    else:
        quota, _nudge = await quota_view(user_id, language)
        body = text(language, "vip_inactive_status", quota=quota)
        markup = InlineKeyboardMarkup(upgrade_keyboard(language).inline_keyboard + back_keyboard(language).inline_keyboard)
    await edit_menu(update, body, reply_markup=markup)


async def start_share_earn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    language = await lang_of(update)
    user_id = update.effective_user.id
    if await users.is_vip(user_id):
        await edit_menu(update, text(language, "share_earn_vip_active"), reply_markup=back_keyboard(language))
        return
    async with Session() as s:
        pending = await s.scalar(select(ShareRequest).where(
            ShareRequest.user_id == user_id, ShareRequest.status == ShareRequestStatus.PENDING.value))
    if pending is not None:
        await edit_menu(update, text(language, "share_earn_already_pending"), reply_markup=back_keyboard(language))
        return
    set_state(context, ST_SHARE_SCREENSHOT)
    await edit_menu(update, text(language, "share_earn_prompt"), reply_markup=back_keyboard(language))


async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if get_state(context) != ST_SHARE_SCREENSHOT:
        return False
    language = await lang_of(update)
    message = update.message
    if not message.photo:
        await message.reply_text(text(language, "share_earn_invalid"))
        return True
    clear_state(context)
    user_id = update.effective_user.id
    async with Session() as s:
        row = ShareRequest(user_id=user_id, status=ShareRequestStatus.PENDING.value)
        s.add(row)
        await s.commit()
        await s.refresh(row)
    u = update.effective_user
    caption = f"👤 {esc(u.full_name)} (@{esc(u.username or '—')})\n🆔 <code>{u.id}</code>"
    kb_rows = [[
        btn(text("ar", "approve_btn"), f"approve_share_{row.id}", style=SUCCESS, emoji=E.SHIELD),
        btn(text("ar", "reject_btn"), f"reject_share_{row.id}", style=DANGER, emoji=E.FORBIDDEN),
    ]]
    try:
        sent = await context.bot.send_photo(settings.admin_id, photo=message.photo[-1].file_id, caption=caption,
                                            reply_markup=InlineKeyboardMarkup(kb_rows))
    except Exception:
        logger.exception("تعذّر إرسال طلب المشاركة للمالك")
        async with Session() as s:
            stale = await s.get(ShareRequest, row.id)
            if stale is not None:
                await s.delete(stale)
                await s.commit()
        await message.reply_text(text(language, "error"))
        return True
    async with Session() as s:
        row2 = await s.get(ShareRequest, row.id)
        row2.admin_message_id = sent.message_id
        await s.commit()
    await message.reply_text(text(language, "share_earn_pending"))
    return True


async def resolve_share(update: Update, context: ContextTypes.DEFAULT_TYPE, approve: bool, request_id: int) -> None:
    if not is_admin(update):
        return
    async with Session() as s:
        row = await s.get(ShareRequest, request_id)
        if row is None or row.status != ShareRequestStatus.PENDING.value:
            return
        row.status = ShareRequestStatus.APPROVED.value if approve else ShareRequestStatus.REJECTED.value
        target_id = row.user_id
        await s.commit()

    if approve:
        await users.grant_vip(target_id, hours=1)
    target_lang = await users.get_language(target_id)
    try:
        await context.bot.send_message(target_id, text(target_lang, "share_earn_approved" if approve
                                                        else "share_earn_rejected"))
    except Exception:
        logger.warning("تعذّر إبلاغ المستخدم %s بنتيجة طلب المشاركة", target_id)
    mark = "✅" if approve else "❌"
    try:
        await update.callback_query.edit_message_caption(
            caption=f"{mark} {update.callback_query.message.caption_html}")
    except Exception:
        pass
