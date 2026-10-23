from functools import partial
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes


from detect_intent_text import detect_intent_text


logger = logging.getLogger(__name__)


class TelegramLogsHandler(logging.Handler):
    """Хендлер, который отправляет логи в Telegram-чат админа."""

    def __init__(self, application, chat_id: str):
        super().__init__()
        self.application = application
        self.chat_id = chat_id

    def emit(self, record: logging.LogRecord) -> None:
        log_entry = self.format(record)
        try:
            self.application.create_task(
                self.application.bot.send_message(
                    chat_id=self.chat_id, text=log_entry
                )
            )
        except Exception:
            self.handleError(record)


async def handle_message(update, context, project_id) -> None:
    """Обрабатывает входящее сообщение через DialogFlow."""

    session_id = f"tg-{update.effective_chat.id}"
    user_text = update.message.text

    try:
        reply = detect_intent_text(
            project_id=project_id,
            session_id=session_id,
            text=user_text,
        ).fulfillment_text

    except Exception:
        logger.exception("TG: ошибка обработки сообщения")
        await update.message.reply_text("Извините, произошла ошибка. Попробуйте позже.")
        return

    await update.message.reply_text(reply)


def main() -> None:
    load_dotenv()
    tg_token = os.environ["TG_TOKEN"]
    logs_chat_id = os.environ["LOGS_TG_CHAT_ID"]
    project_id = os.environ["DIALOGFLOW_PROJECT_ID"]

    logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    application = Application.builder().token(tg_token).build()

    telegram_handler = TelegramLogsHandler(application, logs_chat_id)
    telegram_handler.setLevel(logging.INFO)
    telegram_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(telegram_handler)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, partial(handle_message, project_id=project_id)))

    try:
        application.run_polling()
    except Exception:
        logger.exception("TG-бот упал с ошибкой")
        raise


if __name__ == "__main__":
    main()
