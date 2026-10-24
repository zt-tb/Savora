import asyncio
import io
import logging

from telegram import InputMediaPhoto, Update
from telegram.ext import ContextTypes

from .. import emoji_ids as E
from .. import session_vault, telethon_runtime
from ..buttons import DANGER, PRIMARY, SUCCESS, btn
from ..login_flow import LoginError, NeedsPassword, clear_rate_limits, login_session
from ..texts import text
from ..ui import esc
from .common import InlineKeyboardMarkup, back_keyboard, clear_state, edit_menu, get_state, is_admin, lang_of, set_state

logger = logging.getLogger(__name__)

ST_PHONE = "login_phone"
ST_CODE = "login_code"
ST_PASSWORD = "login_password"
ST_PASSWORD_QR = "login_password_qr"

_qr_task: asyncio.Task | None = None


def _menu_kb(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [btn(text(language, "login_by_phone"), "login_phone_start", style=PRIMARY, emoji=E.PERSON)],
        [btn(text(language, "login_by_qr"), "login_qr_start", style=PRIMARY, emoji=E.SEARCH)],
        [btn(text(language, "login_cancel"), "admin_session", style=DANGER, emoji=E.FORBIDDEN)],
    ])


def _qr_cancel_kb(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[btn(text(language, "login_cancel"), "login_cancel", style=DANGER,
                                      emoji=E.FORBIDDEN)]])


def _candidate_kb(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [btn(text(language, "login_activate_btn"), "login_activate", style=SUCCESS, emoji=E.SHIELD)],
        [btn(text(language, "login_cancel"), "login_cancel", style=DANGER, emoji=E.FORBIDDEN)],
    ])


async def show_session_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    online = await telethon_runtime.is_ready()
    status = text(language, "login_status_on" if online else "login_status_off")
    rows = [[btn(text(language, "login_new_btn"), "login_start_menu", style=PRIMARY, emoji=E.KEY)]]
    if online:
        rows.insert(0, [btn(text(language, "login_logout_btn"), "login_logout", style=DANGER, emoji=E.BIN)])
    rows.append([btn(text(language, "back_btn"), "admin_panel", style=PRIMARY, emoji=E.EYE)])
    await edit_menu(update, 
        f"{status}\n\n{text(language, 'login_menu')}", reply_markup=InlineKeyboardMarkup(rows))


async def show_method_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    clear_state(context)
    await login_session.cancel()
    await edit_menu(update, text(language, "login_menu"), reply_markup=_menu_kb(language))


async def start_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    set_state(context, ST_PHONE)
    await edit_menu(update, text(language, "login_ask_phone"), reply_markup=back_keyboard(language, to="login_start_menu"))


async def start_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global _qr_task
    if not is_admin(update):
        return
    language = await lang_of(update)
    clear_state(context)
    try:
        url = await login_session.begin_qr()
    except LoginError as exc:
        await edit_menu(update, str(exc), reply_markup=_menu_kb(language))
        return
    png = _render_qr(url)
    msg = await update.callback_query.message.reply_photo(
        photo=png, caption=text(language, "login_qr_caption"), parse_mode="HTML",
        reply_markup=_qr_cancel_kb(language))
    if _qr_task is not None and not _qr_task.done():
        _qr_task.cancel()
    _qr_task = asyncio.create_task(_qr_watch(context, msg.chat_id, msg.message_id, language))


def _render_qr(url: str) -> bytes:
    import qrcode

    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


async def _qr_watch(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, language: str) -> None:
    bot = context.bot
    for _ in range(6):
        try:
            result = await login_session.wait_qr()
        except LoginError:
            return
        if result == "need_password":
            set_state(context, ST_PASSWORD_QR)
            context.user_data["_qr_login_chat"] = chat_id
            try:
                await bot.edit_message_caption(chat_id=chat_id, message_id=message_id,
                                               caption=text(language, "login_ask_password"), parse_mode="HTML")
            except Exception:
                pass
            return
        if result == "ok":
            await _finish_login(bot, chat_id, language, edit_message_id=message_id, is_photo=True)
            return
        if result == "expired":
            try:
                url = await login_session.refresh_qr()
            except LoginError:
                return
            png = _render_qr(url)
            try:
                await bot.edit_message_media(
                    media=InputMediaPhoto(png, caption=f"{text(language, 'login_qr_expired')}\n\n"
                                                        f"{text(language, 'login_qr_caption')}",
                                          parse_mode="HTML"),
                    chat_id=chat_id, message_id=message_id, reply_markup=_qr_cancel_kb(language))
            except Exception:
                return


async def handle_text_step(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not is_admin(update):
        return False
    state = get_state(context)
    if state not in (ST_PHONE, ST_CODE, ST_PASSWORD, ST_PASSWORD_QR):
        return False
    message = update.message
    value = (message.text or "").strip()
    try:
        await message.delete()
    except Exception:
        pass
    language = await lang_of(update)
    chat_id = message.chat_id

    if state == ST_PHONE:
        try:
            await login_session.begin_phone(value)
        except LoginError as exc:
            await context.bot.send_message(chat_id, str(exc), reply_markup=_menu_kb(language))
            clear_state(context)
            return True
        set_state(context, ST_CODE)
        await context.bot.send_message(chat_id, text(language, "login_ask_code"),
                                       reply_markup=back_keyboard(language, to="login_start_menu"), parse_mode="HTML")
        return True

    if state == ST_CODE:
        try:
            await login_session.submit_code(value)
        except NeedsPassword:
            set_state(context, ST_PASSWORD)
            await context.bot.send_message(chat_id, text(language, "login_ask_password"),
                                           reply_markup=back_keyboard(language, to="login_start_menu"),
                                           parse_mode="HTML")
            return True
        except LoginError as exc:
            await context.bot.send_message(chat_id, str(exc),
                                           reply_markup=back_keyboard(language, to="login_start_menu"))
            return True
        clear_state(context)
        await _finish_login(context.bot, chat_id, language)
        return True

    if state in (ST_PASSWORD, ST_PASSWORD_QR):
        try:
            await login_session.submit_password(value)
        except LoginError as exc:
            await context.bot.send_message(chat_id, str(exc),
                                           reply_markup=back_keyboard(language, to="login_start_menu"))
            return True
        clear_state(context)
        await _finish_login(context.bot, chat_id, language)
        return True
    return False


async def _finish_login(bot, chat_id: int, language: str, *, edit_message_id: int | None = None,
                        is_photo: bool = False) -> None:
    try:
        meta = await login_session.finish()
    except LoginError as exc:
        await bot.send_message(chat_id, str(exc))
        return
    body = text(language, "login_candidate", name=esc(meta["name"]),
                username=f"@{esc(meta['username'])}" if meta["username"] else "—", id=meta["id"])
    kb = _candidate_kb(language)
    if edit_message_id is not None and is_photo:
        try:
            await bot.edit_message_caption(chat_id=chat_id, message_id=edit_message_id, caption=body,
                                           reply_markup=kb, parse_mode="HTML")
            return
        except Exception:
            pass
    await bot.send_message(chat_id, body, reply_markup=kb, parse_mode="HTML")


async def _reply_candidate_message(update: Update, body: str) -> None:
    query = update.callback_query
    if query.message.photo:
        try:
            await query.edit_message_caption(caption=body)
            return
        except Exception:
            pass
    await query.edit_message_text(body)


async def activate_candidate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    candidate = await session_vault.take_candidate()
    if candidate is None:
        await _reply_candidate_message(update, text(language, "login_no_candidate"))
        return
    session_string, meta = candidate
    ok, info = await telethon_runtime.swap(session_string)
    if not ok:
        await _reply_candidate_message(update, text(language, "login_activate_failed", reason=esc(info)))
        return
    await session_vault.save_session(session_string)
    await clear_rate_limits()
    await _reply_candidate_message(update, text(language, "login_activated", name=esc(info)))


async def cancel_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    clear_state(context)
    await login_session.cancel()
    await session_vault.drop_candidate()
    await _reply_candidate_message(update, text(language, "login_cancelled"))


async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return
    language = await lang_of(update)
    await telethon_runtime.shutdown()
    await session_vault.clear_session()
    await edit_menu(update, text(language, "login_logged_out"))
