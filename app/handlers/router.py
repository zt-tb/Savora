from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from ..texts import text
from . import admin_panel, download, payments, session_login, start
from .common import lang_of

logger = logging.getLogger(__name__)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await session_login.handle_text_step(update, context):
        return
    if await admin_panel.handle_text_step(update, context):
        return
    text_value = update.message.text or ""
    if download.is_download_request(text_value):
        await download.handle_link(update, context)
        return
    language = await lang_of(update)
    await update.message.reply_text(text(language, "send_link"))


async def on_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await admin_panel.handle_media_step(update, context):
        return
    if await start.handle_screenshot(update, context):
        return


CALLBACK_ROUTES = {
    "download": start.ask_download,
    "vip_status": start.show_vip_status,
    "vip_sub": payments.show_vip_sub,
    "change_language": start.show_language_menu,
    "my_id": start.show_my_id,
    "share_earn": start.start_share_earn,
    "back_to_main": start.back_to_main,
    "admin_panel": admin_panel.show_panel,
    "admin_stats": admin_panel.show_stats,
    "admin_broadcast": admin_panel.ask_broadcast,
    "admin_maint": admin_panel.toggle_maintenance,
    "admin_caption": admin_panel.show_caption_menu,
    "admin_caption_reset": admin_panel.reset_caption,
    "admin_welcome": admin_panel.show_welcome_menu,
    "admin_welcome_set": admin_panel.ask_welcome_media,
    "admin_welcome_reset": admin_panel.reset_welcome_media,
    "admin_session": session_login.show_session_panel,
    "login_start_menu": session_login.show_method_menu,
    "login_phone_start": session_login.start_phone,
    "login_qr_start": session_login.start_qr,
    "login_activate": session_login.activate_candidate,
    "login_cancel": session_login.cancel_login,
    "login_logout": session_login.logout,
}

STATE_ROUTES = {
    "admin_add_vip": lambda u, c: admin_panel.ask_id(u, c, admin_panel.ST_ADD_VIP),
    "admin_remove_vip": lambda u, c: admin_panel.ask_id(u, c, admin_panel.ST_REMOVE_VIP),
    "admin_ban": lambda u, c: admin_panel.ask_id(u, c, admin_panel.ST_BAN),
    "admin_unban": lambda u, c: admin_panel.ask_id(u, c, admin_panel.ST_UNBAN),
    "admin_caption_footer": lambda u, c: admin_panel.ask_caption_value(u, c, admin_panel.ST_FOOTER),
    "admin_caption_words": lambda u, c: admin_panel.ask_caption_value(u, c, admin_panel.ST_WORDS),
}


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data or ""

    if data.startswith(download.CANCEL_PREFIX):
        await download.cancel_job(update, context, int(data[len(download.CANCEL_PREFIX):]))
        return

    await query.answer()

    if data in ("lang_ar", "lang_en"):
        await start.set_language(update, context, data.split("_", 1)[1])
        return
    if data.startswith(payments.BUY_PREFIX):
        await payments.buy_plan(update, context, data[len(payments.BUY_PREFIX):])
        return
    if data.startswith("approve_share_"):
        await start.resolve_share(update, context, True, int(data.rsplit("_", 1)[1]))
        return
    if data.startswith("reject_share_"):
        await start.resolve_share(update, context, False, int(data.rsplit("_", 1)[1]))
        return

    if data in STATE_ROUTES:
        await STATE_ROUTES[data](update, context)
        return
    handler = CALLBACK_ROUTES.get(data)
    if handler is not None:
        await handler(update, context)
