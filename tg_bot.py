import logging
import os

from dotenv import load_dotenv
from google.cloud import dialogflow
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
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


def detect_intent_text(project_id, session_id, text, language_code="ru-RU"):
    """Отправляет текст в DialogFlow и возвращает ответ агента."""

    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return response.query_result.fulfillment_text


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает входящее сообщение через DialogFlow."""

    project_id = os.environ["DIALOGFLOW_PROJECT_ID"]
    session_id = str(update.effective_chat.id)
    user_text = update.message.text

    try:
        reply = detect_intent_text(
            project_id=project_id,
            session_id=session_id,
            text=user_text,
        )
        await update.message.reply_text(reply)

    except Exception as e:
        logger.error("TG: ошибка обработки сообщения: %s", e, exc_info=True)
        try:
            await update.message.reply_text(
                "Извините, произошла ошибка. Попробуйте позже."
            )
        except Exception:
            pass


def main() -> None:
    load_dotenv()
    tg_token = os.environ["TG_TOKEN"]
    logs_chat_id = os.environ["LOGS_TG_CHAT_ID"]

    application = Application.builder().token(tg_token).build()

    telegram_handler = TelegramLogsHandler(application, logs_chat_id)
    telegram_handler.setLevel(logging.INFO)
    telegram_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(telegram_handler)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    try:
        application.run_polling()
    except Exception as e:
        logger.error("TG-бот упал с ошибкой: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    main()
