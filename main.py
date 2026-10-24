import logging

from telegram import LinkPreviewOptions, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, Conflict
from telegram.ext import (
    AIORateLimiter,
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    Defaults,
    MessageHandler,
    PreCheckoutQueryHandler,
    TypeHandler,
    filters,
)

from app import antispam, monitor, settings_store, telethon_runtime, ui, users
from app.config import settings
from app.db import init_db
from app.handlers import download, payments
from app.handlers.router import on_callback, on_media, on_text
from app.handlers.start import start
from app.texts import text

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    error = context.error
    if isinstance(error, Conflict):
        logger.warning("Conflict: نسخة ثانية تستخدم نفس التوكن — خلّ Replicas=1 و Overlap=0 وأطفئ أي نسخة ثانية.")
        return
    if isinstance(error, BadRequest) and "emoji" in str(error).lower() and ui.animated_enabled():
        ui.set_animated(False)
        logger.error("رُفض الإيموجي المتحرك (%s) — تحوّلنا لإيموجي عادي", error)
        try:
            language = await users.get_language(settings.admin_id)
            await context.bot.send_message(settings.admin_id, text(language, "emoji_fallback_alert"))
        except Exception:
            logger.debug("تعذّر إبلاغ المالك بتحويل الإيموجي", exc_info=True)
        return
    logger.error("Update %s caused error %s", update, error, exc_info=error)


async def post_init(application: Application) -> None:
    await init_db()
    await settings_store.load()
    await telethon_runtime.bootstrap()
    await download.start_workers()
    if application.job_queue is not None:
        application.job_queue.run_repeating(monitor.health_job, interval=monitor.CHECK_INTERVAL_SECONDS,
                                            first=60, name="ts-health")
    else:
        logger.warning("JobQueue غير متوفر — مراقبة حساب التحميل الدورية معطّلة (ثبّت python-telegram-bot[job-queue])")
    logger.info("✅ Savora بدأ التشغيل")


async def post_shutdown(application: Application) -> None:
    await download.stop_workers()
    await telethon_runtime.shutdown()


def build_application() -> Application:
    defaults = Defaults(parse_mode=ParseMode.HTML, link_preview_options=LinkPreviewOptions(is_disabled=True))
    application = (
        Application.builder()
        .token(settings.bot_token)
        .defaults(defaults)
        .rate_limiter(AIORateLimiter(max_retries=3))
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    application.add_handler(TypeHandler(Update, antispam.guard), group=-1)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("paysupport", payments.paysupport))
    application.add_handler(CommandHandler("terms", payments.terms))
    application.add_handler(CommandHandler("refund", payments.refund))
    application.add_handler(PreCheckoutQueryHandler(payments.precheckout))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, payments.successful_payment))
    application.add_handler(MessageHandler(filters.PHOTO | filters.ANIMATION | filters.VIDEO, on_media))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    application.add_handler(CallbackQueryHandler(on_callback))
    application.add_error_handler(error_handler)
    return application


def main() -> None:
    app = build_application()
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
