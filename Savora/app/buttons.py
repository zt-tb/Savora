import re

from telegram import InlineKeyboardButton

from . import ui

PRIMARY = "primary"
SUCCESS = "success"
DANGER = "danger"


_LEADING_SYMBOLS = re.compile(r"^[\W_]+")


def _icon(text: str, emoji: str | None) -> tuple[str, str | None]:
    if emoji and ui.animated_enabled():
        stripped = _LEADING_SYMBOLS.sub("", text)
        return (stripped or text), emoji
    return text, None


def btn(text: str, callback_data: str, *, style: str = PRIMARY, emoji: str | None = None) -> InlineKeyboardButton:
    text, icon = _icon(text, emoji)
    return InlineKeyboardButton(text=text, callback_data=callback_data, style=style, icon_custom_emoji_id=icon)


def url_btn(text: str, url: str, *, style: str = PRIMARY, emoji: str | None = None) -> InlineKeyboardButton:
    text, icon = _icon(text, emoji)
    return InlineKeyboardButton(text=text, url=url, style=style, icon_custom_emoji_id=icon)


def web_app_btn(text: str, web_app, *, style: str = PRIMARY, emoji: str | None = None) -> InlineKeyboardButton:
    text, icon = _icon(text, emoji)
    return InlineKeyboardButton(text=text, web_app=web_app, style=style, icon_custom_emoji_id=icon)
