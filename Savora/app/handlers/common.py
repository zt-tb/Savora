from __future__ import annotations

from contextlib import suppress

from telegram import InlineKeyboardMarkup, Update
from telegram.error import BadRequest, TelegramError
from telegram.ext import ContextTypes

from .. import emoji_ids as E
from .. import users
from ..buttons import DANGER, PRIMARY, SUCCESS, btn, url_btn
from ..config import settings
from ..plans import per_day_stars
from ..texts import text
from ..ui import human_delta
from ..users import get_language


STATE_KEY = "ts_state"


def is_admin(update: Update) -> bool:
    user = update.effective_user
    return bool(user and user.id == settings.admin_id)


async def lang_of(update: Update) -> str:
    user = update.effective_user
    if not user:
        return "ar"
    return await get_language(user.id)


def clear_state(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop(STATE_KEY, None)


def set_state(context: ContextTypes.DEFAULT_TYPE, state: str) -> None:
    context.user_data[STATE_KEY] = state


def get_state(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    return context.user_data.get(STATE_KEY)


async def edit_menu(update: Update, body: str, reply_markup: InlineKeyboardMarkup | None = None) -> None:
    query = update.callback_query
    try:
        await query.edit_message_text(body, reply_markup=reply_markup)
    except BadRequest as exc:
        reason = str(exc).lower()
        if "not modified" in reason:
            return
        if "no text" not in reason:
            raise
        message = query.message
        await message.get_bot().send_message(message.chat_id, body, reply_markup=reply_markup)
        with suppress(TelegramError):
            await message.delete()


async def quota_view(user_id: int, language: str) -> tuple[str, str]:
    left = await users.quota_left(user_id)
    if left is None:
        return text(language, "left_unlimited"), ""
    per_day = per_day_stars()
    if left > 0:
        meter = "▰" * left + "▱" * (users.FREE_LIMIT - left)
        return (text(language, "quota_meter", meter=meter, left=left, total=users.FREE_LIMIT),
                text(language, "nudge_left", per_day=per_day))
    wait = await users.wait_remaining(user_id) or users.COOLDOWN
    return (text(language, "quota_locked", wait=human_delta(wait, language)),
            text(language, "nudge_locked", per_day=per_day))


def upgrade_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [btn(text(language, "upgrade_btn"), "vip_sub", style=SUCCESS, emoji=E.MEDAL)],
        [btn(text(language, "share_earn_btn"), "share_earn", style=PRIMARY, emoji=E.HEART)],
    ])


def main_keyboard(language: str, *, show_admin: bool, vip: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [btn(text(language, "download_btn"), "download", style=SUCCESS, emoji=E.ZAP)],
        [
            btn(text(language, "vip_status_btn"), "vip_status", style=PRIMARY, emoji=E.TROPHY),
            btn(text(language, "vip_sub_btn" if vip else "upgrade_btn"), "vip_sub",
                style=PRIMARY if vip else SUCCESS, emoji=E.MEDAL),
        ],
        [
            btn(text(language, "change_lang_btn"), "change_language", style=PRIMARY, emoji=E.PERSON),
            btn(text(language, "my_id_btn"), "my_id", style=PRIMARY, emoji=E.KEY),
            btn(text(language, "share_earn_btn"), "share_earn", style=SUCCESS, emoji=E.HEART),
        ],
        [url_btn(text(language, "contact_btn"), "https://t.me/K0_MG", style=PRIMARY, emoji=E.MAIL)],
    ]
    if show_admin:
        rows[-1].append(btn(text(language, "admin_panel_btn"), "admin_panel", style=DANGER, emoji=E.SHIELD))
    return InlineKeyboardMarkup(rows)


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        btn("🇮🇶 العربية", "lang_ar", style=PRIMARY),
        btn("🇬🇧 English", "lang_en", style=PRIMARY),
    ]])


def back_keyboard(language: str, *, to: str = "back_to_main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[btn(text(language, "back_btn"), to, style=PRIMARY, emoji=E.EYE)]])
