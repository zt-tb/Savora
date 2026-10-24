from __future__ import annotations

import logging
from datetime import timedelta

from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from .. import emoji_ids as E
from .. import settings_store, telethon_runtime, users, welcome_media
from ..duration import parse_hours
from ..buttons import DANGER, PRIMARY, SUCCESS, btn
from ..texts import text
from ..ui import esc, human_delta
from . import download
from .common import back_keyboard, clear_state, edit_menu, get_state, is_admin, lang_of, set_state

logger = logging.getLogger(__name__)

ST_ADD_VIP = "admin_add_vip"
ST_REMOVE_VIP = "admin_remove_vip"
ST_BAN = "admin_ban"
ST_UNBAN = "admin_unban"
ST_BROADCAST = "admin_broadcast"
ST_FOOTER = "admin_caption_footer"
ST_WORDS = "admin_caption_words"
ST_WELCOME = "admin_welcome_media"
ST_VIP_DURATION = "admin_vip_duration"
VIP_TARGET_KEY = "ts_vip_target"
ID_STATES = (ST_ADD_VIP, ST_REMOVE_VIP, ST_BAN, ST_UNBAN)
ALL_STATES = ID_STATES + (ST_BROADCAST, ST_FOOTER, ST_WORDS, ST_VIP_DURATION)
MAX_FOOTER = 200
MAX_WORDS = 500


def _panel_kb(language: str) -> InlineKeyboardMarkup:
    maint = settings_store.maintenance_on()
    return InlineKeyboardMarkup([
        [
            btn(text(language, "admin_add_vip"), "admin_add_vip", style=SUCCESS, emoji=E.TROPHY),
            btn(text(language, "admin_remove_vip"), "admin_remove_vip", style=DANGER, emoji=E.FORBIDDEN),
        ],
        [
            btn(text(language, "admin_ban"), "admin_ban", style=DANGER, emoji=E.SKULL),
            btn(text(language, "admin_unban"), "admin_unban", style=SUCCESS, emoji=E.SHIELD),
        ],
        [
            btn(text(language, "admin_stats"), "admin_stats", style=PRIMARY, emoji=E.SEARCH),
            btn(text(language, "admin_broadcast"), "admin_broadcast", style=PRIMARY, emoji=E.MAIL),
        ],
        [
            btn(text(language, "admin_caption_btn"), "admin_caption", style=PRIMARY, emoji=E.MAIL),
            btn(text(language, "admin_welcome_btn"), "admin_welcome", style=PRIMARY, emoji=E.COMET),
        ],
        [
            btn(text(language, "admin_maint_on_btn" if maint else "admin_maint_off_btn"), "admin_maint",
                style=SUCCESS if maint else DANGER, emoji=E.SHIELD),
            btn(text(language, "admin_session"), "admin_session", style=PRIMARY, emoji=E.KEY),
        ],
        [btn(text(language, "back_btn"), "back_to_main", style=PRIMARY, emoji=E.EYE)],
    ])


def _caption_kb(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            btn(text(language, "caption_footer_btn"), "admin_caption_footer", style=PRIMARY, emoji=E.MAIL),
            btn(text(language, "caption_words_btn"), "admin_caption_words", style=PRIMARY, emoji=E.BIN),
        ],
        [
            btn(text(language, "caption_reset_btn"), "admin_caption_reset", style=DANGER, emoji=E.FORBIDDEN),
            btn(text(language, "back_btn"), "admin_panel", style=PRIMARY, emoji=E.EYE),
        ],
    ])


def _welcome_kb(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            btn(text(language, "welcome_set_btn"), "admin_welcome_set", style=SUCCESS, emoji=E.COMET),
            btn(text(language, "welcome_reset_btn"), "admin_welcome_reset", style=DANGER, emoji=E.FORBIDDEN),
        ],
        [btn(text(language, "back_btn"), "admin_panel", style=PRIMARY, emoji=E.EYE)],
    ])


async def show_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    clear_state(context)
    await edit_menu(update, text(language, "admin_panel_title"), reply_markup=_panel_kb(language))


async def ask_id(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    set_state(context, state)
    await edit_menu(update, text(language, "enter_user_id"), reply_markup=back_keyboard(language, to="admin_panel"))


def _lines(rows, fmt) -> str:
    return "".join(fmt(i, row) for i, row in enumerate(rows, 1)) or text("ar", "stats_none")


def render_stats(language: str, st: dict, *, account_ok: bool, queued: int, running: int) -> str:
    return text(
        language, "stats_card",
        users=st["users"], vip=st["vip"], banned=st["banned"],
        today=st["today"], today_ok=st["today_ok"], today_failed=st["today_failed"],
        total=st["total"], rate=st["rate"],
        top=_lines(st["top"], lambda i, r: f"\n  {i}. {esc(r[0])} — <b>{r[2]}</b>"),
        reasons=_lines(st["reasons"], lambda i, r: f"\n  <code>{esc(r[0])}</code> — <b>{r[1]}</b>"),
        account=text(language, "account_ok" if account_ok else "account_off"),
        queued=queued, running=running, stars=st["stars"], sales=st["sales"])


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    st = await users.stats()
    body = render_stats(language, st, account_ok=await telethon_runtime.is_ready(),
                        queued=download.queue.size(), running=download.queue.running())
    await edit_menu(update, body, reply_markup=back_keyboard(language, to="admin_panel"))


async def ask_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    set_state(context, ST_BROADCAST)
    await edit_menu(update, text(language, "broadcast_prompt"), reply_markup=back_keyboard(language, to="admin_panel"))


async def toggle_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    now_on = not settings_store.maintenance_on()
    await settings_store.set_value(settings_store.MAINTENANCE, "1" if now_on else "0")
    body = f"{text(language, 'maint_now_on' if now_on else 'maint_now_off')}\n\n{text(language, 'admin_panel_title')}"
    await edit_menu(update, body, reply_markup=_panel_kb(language))


def _welcome_summary(language: str) -> str:
    chosen = welcome_media.custom()
    current = text(language, f"welcome_current_{chosen[0]}" if chosen else "welcome_current_default")
    return text(language, "welcome_menu", current=current)


async def show_welcome_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    clear_state(context)
    await edit_menu(update, _welcome_summary(language), reply_markup=_welcome_kb(language))


async def ask_welcome_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    set_state(context, ST_WELCOME)
    await edit_menu(update, text(language, "welcome_ask"), reply_markup=back_keyboard(language, to="admin_welcome"))


async def reset_welcome_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    await settings_store.delete(settings_store.WELCOME_MEDIA)
    await edit_menu(update, f"{text(language, 'welcome_reset_done')}\n\n{_welcome_summary(language)}",
                    reply_markup=_welcome_kb(language))


async def handle_media_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not is_admin(update) or get_state(context) != ST_WELCOME:
        return False
    language = await lang_of(update)
    found = welcome_media.extract(update.message)
    if found is None:
        await update.message.reply_text(text(language, "welcome_ask"))
        return True
    clear_state(context)
    await settings_store.set_value(settings_store.WELCOME_MEDIA, f"{found[0]}:{found[1]}")
    await update.message.reply_text(f"{text(language, 'welcome_saved')}\n\n{_welcome_summary(language)}",
                                    reply_markup=_welcome_kb(language))
    return True


def _caption_summary(language: str) -> str:
    footer = settings_store.get(settings_store.CAPTION_FOOTER)
    words = settings_store.blocked_words()
    footer_view = (text(language, "caption_none") if footer == "-"
                   else esc(footer) if footer else text(language, "caption_default"))
    words_view = esc(", ".join(words)) if words else text(language, "caption_none")
    return text(language, "caption_menu", footer=footer_view, words=words_view)


async def show_caption_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    clear_state(context)
    await edit_menu(update, _caption_summary(language), reply_markup=_caption_kb(language))


async def ask_caption_value(update: Update, context: ContextTypes.DEFAULT_TYPE, state: str) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    set_state(context, state)
    await edit_menu(update, 
        text(language, "caption_ask_footer" if state == ST_FOOTER else "caption_ask_words"),
        reply_markup=back_keyboard(language, to="admin_caption"))


async def reset_caption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    await settings_store.delete(settings_store.CAPTION_FOOTER)
    await settings_store.delete(settings_store.BLOCKED_WORDS)
    await edit_menu(update, 
        f"{text(language, 'caption_reset_done')}\n\n{_caption_summary(language)}", reply_markup=_caption_kb(language))


async def handle_text_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not is_admin(update):
        return False
    state = get_state(context)
    if state not in ALL_STATES:
        return False
    message = update.message
    language = await lang_of(update)

    if state == ST_BROADCAST:
        clear_state(context)
        await _run_broadcast(update, context, message)
        return True

    if state in (ST_FOOTER, ST_WORDS):
        clear_state(context)
        value = (message.text or "").strip()
        if state == ST_FOOTER:
            await settings_store.set_value(settings_store.CAPTION_FOOTER, value[:MAX_FOOTER])
        else:
            await settings_store.set_value(settings_store.BLOCKED_WORDS, value[:MAX_WORDS])
        await message.reply_text(f"{text(language, 'caption_saved')}\n\n{_caption_summary(language)}",
                                 reply_markup=_caption_kb(language))
        return True

    raw = (message.text or "").strip()

    if state == ST_VIP_DURATION:
        return await _finish_vip_grant(update, context, raw, language)

    if not raw.lstrip("-").isdigit():
        await message.reply_text(text(language, "invalid_id"), reply_markup=back_keyboard(language, to="admin_panel"))
        return True
    target = int(raw)
    clear_state(context)

    if state == ST_ADD_VIP:
        if not await users.exists(target):
            await message.reply_text(text(language, "user_not_found"), reply_markup=_panel_kb(language))
            return True
        context.user_data[VIP_TARGET_KEY] = target
        set_state(context, ST_VIP_DURATION)
        await message.reply_text(text(language, "vip_ask_duration", target),
                                 reply_markup=back_keyboard(language, to="admin_panel"))
        return True

    actions = {
        ST_REMOVE_VIP: (users.revoke_vip, "vip_removed"),
        ST_BAN: (lambda uid: users.set_banned(uid, True), "user_banned"),
        ST_UNBAN: (lambda uid: users.set_banned(uid, False), "user_unbanned"),
    }
    func, ok_key = actions[state]
    ok = await func(target)
    body = text(language, ok_key, target) if ok else text(language, "user_not_found")
    await message.reply_text(body, reply_markup=_panel_kb(language))
    return True


async def _finish_vip_grant(update: Update, context: ContextTypes.DEFAULT_TYPE, raw: str, language: str) -> bool:
    message = update.message
    target = context.user_data.get(VIP_TARGET_KEY)
    if target is None:
        clear_state(context)
        await message.reply_text(text(language, "invalid_id"), reply_markup=_panel_kb(language))
        return True
    hours = parse_hours(raw)
    if hours is None:
        await message.reply_text(text(language, "vip_bad_duration"), reply_markup=back_keyboard(language, to="admin_panel"))
        return True
    clear_state(context)
    context.user_data.pop(VIP_TARGET_KEY, None)
    if not await users.grant_vip(target, hours=hours):
        await message.reply_text(text(language, "user_not_found"), reply_markup=_panel_kb(language))
        return True
    await message.reply_text(text(language, "vip_added", target, human_delta(timedelta(hours=hours), language)),
                             reply_markup=_panel_kb(language))
    target_language = await users.get_language(target)
    try:
        await context.bot.send_message(target, text(target_language, "vip_gift_notice",
                                                    human_delta(timedelta(hours=hours), target_language)))
    except Exception:
        logger.info("تعذّر إبلاغ المستخدم %s بتفعيل VIP", target, exc_info=True)
    return True


async def _run_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE, message) -> None:
    language = await lang_of(update)
    ids = await users.all_user_ids()
    status = await message.reply_text(text(language, "broadcast_started", len(ids)))
    ok = failed = 0
    for uid in ids:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=message.chat_id, message_id=message.message_id)
            ok += 1
        except Exception:
            failed += 1
    await status.edit_text(text(language, "broadcast_done", ok, failed), reply_markup=_panel_kb(language))
