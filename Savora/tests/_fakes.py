from __future__ import annotations

import os


class FakeUser:
    def __init__(self, id=1001, full_name="علي <b>", first_name="علي", username="ali"):
        self.id, self.full_name, self.first_name, self.username = id, full_name, first_name, username


class FakeBot:
    def __init__(self, username="TestBot"):
        self.username = username
        self.sent, self.invoices, self.refunds = [], [], []
        self.fail_refund = False

    async def send_message(self, chat_id, text, **kw):
        self.sent.append((chat_id, text, kw))
        return FakeMessage(text=text, bot=self, chat_id=chat_id)

    async def send_invoice(self, **kw):
        self.invoices.append(kw)

    async def refund_star_payment(self, user_id, telegram_payment_charge_id):
        if self.fail_refund:
            raise RuntimeError("CHARGE_NOT_FOUND")
        self.refunds.append((user_id, telegram_payment_charge_id))


class FakeMessage:

    def __init__(self, text="", bot=None, chat_id=1, photo=None, caption=None, user=None):
        self.text, self.bot, self.chat_id, self.photo, self.caption = text, bot or FakeBot(), chat_id, photo, caption
        self.from_user = user
        self.successful_payment = None
        self.replies, self.edits = [], []
        self.deleted = False
        self.fail_edit = False

    @property
    def caption_html(self):
        return self.caption or ""

    def get_bot(self):
        return self.bot

    async def reply_text(self, text, **kw):
        self.replies.append(("text", text, kw))
        return FakeMessage(text=text, bot=self.bot, chat_id=self.chat_id)

    async def edit_text(self, text, **kw):
        if self.fail_edit:
            raise RuntimeError("message to edit not found")
        self.edits.append((text, kw))
        self.text = text

    async def delete(self):
        self.deleted = True

    def _file(self, kind, fh, kw):
        data = fh.read() if hasattr(fh, "read") else getattr(getattr(fh, "obj", None), "read", lambda: b"")()
        self.replies.append((kind, len(data), kw))
        return FakeMessage(bot=self.bot, chat_id=self.chat_id)

    async def reply_photo(self, fh, **kw):
        return self._file("photo", fh, kw)

    async def reply_video(self, fh, **kw):
        return self._file("video", fh, kw)

    async def reply_document(self, fh, **kw):
        return self._file("document", fh, kw)

    async def reply_audio(self, fh, **kw):
        return self._file("audio", fh, kw)

    async def reply_voice(self, fh, **kw):
        return self._file("voice", fh, kw)

    async def reply_animation(self, fh, **kw):
        return self._file("animation", fh, kw)

    async def reply_sticker(self, fh, **kw):
        return self._file("sticker", fh, kw)

    async def reply_media_group(self, media, **kw):
        sizes = []
        for item in media:
            fh = item.media
            sizes.append((type(item).__name__, len(fh.read()), item.caption))
        self.replies.append(("group", sizes, kw))
        return [FakeMessage(bot=self.bot, chat_id=self.chat_id) for _ in media]


class FakeQuery:
    def __init__(self, data="", message=None, user=None):
        self.data, self.message = data, message or FakeMessage()
        self.from_user = user
        self.answers = []
        self.edits = []

    async def answer(self, text=None, show_alert=False, **kw):
        self.answers.append((text, show_alert))

    async def edit_message_text(self, text, **kw):
        self.edits.append((text, kw))

    async def edit_message_caption(self, caption=None, **kw):
        self.edits.append((caption, kw))


class FakeUpdate:
    def __init__(self, user=None, message=None, query=None):
        self.effective_user = user or FakeUser()
        self.message = message
        self.callback_query = query
        self.effective_chat = type("C", (), {"id": 5555})()
        self.pre_checkout_query = None


class FakeContext:
    def __init__(self, bot=None, args=None):
        self.bot = bot or FakeBot()
        self.user_data = {}
        self.args = args or []
        self.error = None


class FakeMedia:
    def __init__(self, photo=None, document=None):
        self.photo, self.document = photo, document


class FakeTLMessage:
    def __init__(self, id, media=None, text="", grouped_id=None):
        self.id, self.media, self.text, self.grouped_id = id, media, text, grouped_id
        self.message = text


class FakeTelethon:

    def __init__(self, messages=None, stories=None, connected=True, size=2048):
        self.messages = messages or {}
        self.stories = stories or []
        self.connected = connected
        self.size = size
        self.downloaded = []
        self.raise_on = None

    def is_connected(self):
        return self.connected

    async def get_messages(self, chat, ids=None):
        if self.raise_on:
            raise self.raise_on
        if isinstance(ids, list):
            return [self.messages.get(i) for i in ids]
        return self.messages.get(ids)

    async def get_entity(self, chat):
        return ("entity", chat)

    async def __call__(self, request):
        return type("R", (), {"stories": self.stories})()

    async def download_media(self, media, file=None, progress_callback=None):
        if self.raise_on:
            raise self.raise_on
        path = os.path.join(file, f"file_{len(self.downloaded)}.bin")
        with open(path, "wb") as fh:
            fh.write(b"x" * self.size)
        if progress_callback:
            progress_callback(self.size, self.size)
        self.downloaded.append(media)
        return path
