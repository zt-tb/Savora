from __future__ import annotations

import os
import sys
import types


def _mod(name: str) -> types.ModuleType:
    m = sys.modules.get(name)
    if m is None:
        m = types.ModuleType(name)
        sys.modules[name] = m
    return m


telegram = _mod("telegram")


class InlineKeyboardButton:
    def __init__(self, text=None, callback_data=None, url=None, web_app=None,
                 style=None, icon_custom_emoji_id=None, **kw):
        self.text = text
        self.callback_data = callback_data
        self.url = url
        self.web_app = web_app
        self.style = style
        self.icon_custom_emoji_id = icon_custom_emoji_id
        for k, v in kw.items():
            setattr(self, k, v)


class InlineKeyboardMarkup:
    def __init__(self, rows):
        self.inline_keyboard = rows


class InputFile:
    def __init__(self, obj, filename=None):
        self.obj = obj
        self.filename = filename


class InputMediaPhoto:
    def __init__(self, media, caption=None, **kw):
        self.media = media
        self.caption = caption
        for k, v in kw.items():
            setattr(self, k, v)


class _InputMedia:
    def __init__(self, media, caption=None, **kw):
        self.media = media
        self.caption = caption
        for k, v in kw.items():
            setattr(self, k, v)


class InputMediaVideo(_InputMedia):
    pass


class InputMediaAudio(_InputMedia):
    pass


class InputMediaDocument(_InputMedia):
    pass


class LabeledPrice:
    def __init__(self, label, amount):
        self.label = label
        self.amount = amount


class LinkPreviewOptions:
    def __init__(self, **kw):
        self.kw = kw


class Update:
    ALL_TYPES = object()


telegram.InlineKeyboardButton = InlineKeyboardButton
telegram.InlineKeyboardMarkup = InlineKeyboardMarkup
telegram.InputFile = InputFile
telegram.InputMediaPhoto = InputMediaPhoto
telegram.Update = Update
telegram.InputMediaVideo = InputMediaVideo
telegram.InputMediaAudio = InputMediaAudio
telegram.InputMediaDocument = InputMediaDocument
telegram.LabeledPrice = LabeledPrice
telegram.LinkPreviewOptions = LinkPreviewOptions

telegram_constants = _mod("telegram.constants")


class ParseMode:
    HTML = "HTML"


telegram_constants.ParseMode = ParseMode
telegram.constants = telegram_constants

telegram_error = _mod("telegram.error")


class TelegramError(Exception):
    pass


class BadRequest(TelegramError):
    pass


class Conflict(TelegramError):
    pass


telegram_error.TelegramError = TelegramError
telegram_error.BadRequest = BadRequest
telegram_error.Conflict = Conflict
telegram.error = telegram_error

telegram_ext = _mod("telegram.ext")


class _Filter:
    def __invert__(self):
        return self

    def __and__(self, other):
        return self

    def __or__(self, other):
        return self


class _Filters:
    PHOTO = _Filter()
    ANIMATION = _Filter()
    VIDEO = _Filter()
    TEXT = _Filter()
    COMMAND = _Filter()
    SUCCESSFUL_PAYMENT = _Filter()


class ContextTypes:
    DEFAULT_TYPE = object


class _Handler:
    def __init__(self, *a, **kw):
        self.args = a
        self.kwargs = kw


class CommandHandler(_Handler):
    pass


class MessageHandler(_Handler):
    pass


class CallbackQueryHandler(_Handler):
    pass


class PreCheckoutQueryHandler(_Handler):
    pass


class TypeHandler(_Handler):
    pass


class ApplicationHandlerStop(Exception):
    pass


class AIORateLimiter:
    def __init__(self, **kw):
        self.kw = kw


class Defaults:
    def __init__(self, **kw):
        self.kw = kw


class _FakeJobQueue:
    def __init__(self):
        self.jobs = []

    def run_repeating(self, callback, interval, first=None, name=None, **kw):
        self.jobs.append((callback, interval, first, name))


class Application:
    def __init__(self):
        self.handlers = []
        self.error_handlers = []
        self.post_init_cb = None
        self.post_shutdown_cb = None
        self.token = None
        self.defaults = None
        self.rate_limiter = None
        self.job_queue = _FakeJobQueue()

    def add_handler(self, h, group=0):
        self.handlers.append(h)
        self.groups = getattr(self, 'groups', [])
        self.groups.append(group)

    def add_error_handler(self, f):
        self.error_handlers.append(f)

    def run_polling(self, **kw):
        pass


class _AppBuilder:
    def __init__(self):
        self.app = Application()

    def token(self, t):
        self.app.token = t
        return self

    def post_init(self, f):
        self.app.post_init_cb = f
        return self

    def defaults(self, d):
        self.app.defaults = d
        return self

    def rate_limiter(self, r):
        self.app.rate_limiter = r
        return self

    def post_shutdown(self, f):
        self.app.post_shutdown_cb = f
        return self

    def build(self):
        return self.app


Application.builder = staticmethod(lambda: _AppBuilder())

telegram_ext.Application = Application
telegram_ext.PreCheckoutQueryHandler = PreCheckoutQueryHandler
telegram_ext.TypeHandler = TypeHandler
telegram_ext.ApplicationHandlerStop = ApplicationHandlerStop
telegram_ext.AIORateLimiter = AIORateLimiter
telegram_ext.Defaults = Defaults
telegram_ext.CallbackQueryHandler = CallbackQueryHandler
telegram_ext.CommandHandler = CommandHandler
telegram_ext.ContextTypes = ContextTypes
telegram_ext.MessageHandler = MessageHandler
telegram_ext.filters = _Filters()
telegram.ext = telegram_ext


telethon = _mod("telethon")


class TelegramClient:

    def __init__(self, *a, **kw):
        pass


telethon.TelegramClient = TelegramClient

telethon_sessions = _mod("telethon.sessions")


class StringSession:
    def __init__(self, value=None):
        self.value = value


telethon_sessions.StringSession = StringSession
telethon.sessions = telethon_sessions

telethon_errors = _mod("telethon.errors")


class RPCError(Exception):
    pass


class ChannelPrivateError(RPCError):
    pass


class ChatAdminRequiredError(RPCError):
    pass


class FloodWaitError(RPCError):
    def __init__(self, seconds=0):
        super().__init__(f"flood wait {seconds}")
        self.seconds = seconds


class PasswordHashInvalidError(RPCError):
    pass


class PhoneCodeExpiredError(RPCError):
    pass


class PhoneCodeInvalidError(RPCError):
    pass


class PhoneNumberInvalidError(RPCError):
    pass


class SessionPasswordNeededError(RPCError):
    pass


class StoryIdEmptyError(RPCError):
    pass


class AuthKeyDuplicatedError(RPCError):
    pass


class AuthKeyUnregisteredError(RPCError):
    pass


class SessionExpiredError(RPCError):
    pass


class SessionRevokedError(RPCError):
    pass


class UserDeactivatedBanError(RPCError):
    pass


class UserDeactivatedError(RPCError):
    pass


for _name, _cls in [
    ("RPCError", RPCError),
    ("ChannelPrivateError", ChannelPrivateError),
    ("ChatAdminRequiredError", ChatAdminRequiredError),
    ("FloodWaitError", FloodWaitError),
    ("PasswordHashInvalidError", PasswordHashInvalidError),
    ("PhoneCodeExpiredError", PhoneCodeExpiredError),
    ("PhoneCodeInvalidError", PhoneCodeInvalidError),
    ("PhoneNumberInvalidError", PhoneNumberInvalidError),
    ("SessionPasswordNeededError", SessionPasswordNeededError),
    ("StoryIdEmptyError", StoryIdEmptyError),
    ("AuthKeyDuplicatedError", AuthKeyDuplicatedError),
    ("AuthKeyUnregisteredError", AuthKeyUnregisteredError),
    ("SessionExpiredError", SessionExpiredError),
    ("SessionRevokedError", SessionRevokedError),
    ("UserDeactivatedBanError", UserDeactivatedBanError),
    ("UserDeactivatedError", UserDeactivatedError),
]:
    setattr(telethon_errors, _name, _cls)
telethon.errors = telethon_errors

telethon_tl = _mod("telethon.tl")
telethon_tl_types = _mod("telethon.tl.types")
telethon_tl_functions = _mod("telethon.tl.functions")
telethon_tl_functions_stories = _mod("telethon.tl.functions.stories")


class GetStoriesByIDRequest:
    def __init__(self, peer=None, id=None):
        self.peer = peer
        self.id = id


telethon_tl_functions_stories.GetStoriesByIDRequest = GetStoriesByIDRequest
telethon_tl_functions.stories = telethon_tl_functions_stories
telethon_tl.functions = telethon_tl_functions


class DocumentAttributeAnimated:
    pass


class DocumentAttributeAudio:
    def __init__(self, voice=False, **kw):
        self.voice = voice


class DocumentAttributeSticker:
    pass


class DocumentAttributeVideo:
    pass


telethon_tl_types.DocumentAttributeAnimated = DocumentAttributeAnimated
telethon_tl_types.DocumentAttributeAudio = DocumentAttributeAudio
telethon_tl_types.DocumentAttributeSticker = DocumentAttributeSticker
telethon_tl_types.DocumentAttributeVideo = DocumentAttributeVideo
telethon_tl.types = telethon_tl_types
telethon.tl = telethon_tl


sqlalchemy = _mod("sqlalchemy")


class _Type:
    def __call__(self, *a, **kw):
        return self

    def __getitem__(self, item):
        return self


def _unique_constraint(*a, **kw):
    return None


class _Func:
    def __getattr__(self, name):
        def _f(*a, **kw):
            return None
        return _f


class _Select:
    def where(self, *a, **kw):
        return self


def _select(*a, **kw):
    return _Select()


def _text(*a, **kw):
    return a[0] if a else ""


sqlalchemy.BigInteger = _Type()
sqlalchemy.Boolean = _Type()
sqlalchemy.DateTime = _Type()
sqlalchemy.Integer = _Type()
sqlalchemy.String = _Type()
sqlalchemy.UniqueConstraint = _unique_constraint
sqlalchemy.Index = lambda *a, **k: ("index", a, k)
sqlalchemy.func = _Func()
sqlalchemy.select = _select
sqlalchemy.text = _text

sqlalchemy_orm = _mod("sqlalchemy.orm")


class DeclarativeBase:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _Mapped:
    def __class_getitem__(cls, item):
        return cls


def _mapped_column(*a, **kw):
    return None


sqlalchemy_orm.DeclarativeBase = DeclarativeBase
sqlalchemy_orm.Mapped = _Mapped
sqlalchemy_orm.mapped_column = _mapped_column
sqlalchemy.orm = sqlalchemy_orm

sqlalchemy_ext = _mod("sqlalchemy.ext")
sqlalchemy_ext_asyncio = _mod("sqlalchemy.ext.asyncio")


class AsyncSession:
    pass


class _FakeAsyncSessionCM:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def scalar(self, *a, **kw):
        return None

    async def scalars(self, *a, **kw):
        return []

    async def execute(self, *a, **kw):
        return None

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

    async def get(self, model, pk):
        return None

    def add(self, obj):
        pass

    async def delete(self, obj):
        pass


def _create_async_engine(*a, **kw):
    return object()


def _async_sessionmaker(*a, **kw):
    def _factory():
        return _FakeAsyncSessionCM()
    return _factory


sqlalchemy_ext_asyncio.AsyncSession = AsyncSession
sqlalchemy_ext_asyncio.async_sessionmaker = _async_sessionmaker
sqlalchemy_ext_asyncio.create_async_engine = _create_async_engine
sqlalchemy_ext.asyncio = sqlalchemy_ext_asyncio
sqlalchemy.ext = sqlalchemy_ext


redis_mod = _mod("redis")


class FakeRedis:

    def __init__(self):
        self.store: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def ping(self):
        return True

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value
        if ex is not None:
            self.ttls[key] = ex
        return True

    async def delete(self, key):
        existed = key in self.store
        self.store.pop(key, None)
        self.ttls.pop(key, None)
        return 1 if existed else 0

    async def incr(self, key):
        n = int(self.store.get(key, "0")) + 1
        self.store[key] = str(n)
        return n

    async def expire(self, key, seconds):
        self.ttls[key] = seconds
        return True

    async def ttl(self, key):
        return self.ttls.get(key, -1 if key in self.store else -2)

    @classmethod
    def from_url(cls, *a, **kw):
        return cls()


redis_asyncio = _mod("redis.asyncio")
redis_asyncio.Redis = FakeRedis
redis_mod.asyncio = redis_asyncio


pydantic_settings = _mod("pydantic_settings")


class SettingsConfigDict(dict):
    pass


def _accepts_int(typ) -> bool:
    if typ is int:
        return True
    args = getattr(typ, "__args__", None)
    return bool(args) and int in args


def _is_optional(typ) -> bool:
    args = getattr(typ, "__args__", None)
    return bool(args) and type(None) in args


class BaseSettings:
    model_config: dict = {}

    def __init__(self, **overrides):
        ann = {}
        for klass in reversed(type(self).__mro__):
            ann.update(getattr(klass, "__annotations__", {}))
        for name, typ in ann.items():
            if name == "model_config":
                continue
            env_name = name.upper()
            if name in overrides:
                value = overrides[name]
            elif env_name in os.environ:
                value = os.environ[env_name]
            else:
                value = getattr(type(self), name, None)
                if value is None and not _is_optional(typ):
                    raise ValueError(f"متغيّر بيئة ناقص: {env_name}")
            if isinstance(value, str) and _accepts_int(typ):
                value = int(value)
            setattr(self, name, value)


pydantic_settings.BaseSettings = BaseSettings
pydantic_settings.SettingsConfigDict = SettingsConfigDict


qrcode_mod = _mod("qrcode")


class _FakeQrImage:
    def save(self, buf, format=None):
        buf.write(b"FAKE-PNG-BYTES")


def _make(data):
    return _FakeQrImage()


qrcode_mod.make = _make


os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("ADMIN_ID", "7249021797")
os.environ.setdefault("API_ID", "12345")
os.environ.setdefault("API_HASH", "test-api-hash")
os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SESSION_ENCRYPTION_KEY", __import__("base64").urlsafe_b64encode(b"0" * 32).decode())
