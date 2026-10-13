import logging
import os

from dotenv import load_dotenv
from google.cloud import dialogflow
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)


logger = logging.getLogger(__name__)


def detect_intent_text(project_id, session_id, text, language_code="ru-RU"):
    """Send text to DialogFlow and return the agent's response."""

    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return response.query_result.fulfillment_text


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and respond using DialogFlow."""

    project_id = os.environ["DIALOGFLOW_PROJECT_ID"]
    session_id = str(update.effective_chat.id)

    reply = detect_intent_text(
        project_id=project_id,
        session_id=session_id,
        text=update.message.text,
    )

    await update.message.reply_text(reply)


def main() -> None:
    """Start the bot."""

    load_dotenv()
    tg_token = os.environ['TG_TOKEN']

    application = Application.builder().token(tg_token).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()


if __name__ == '__main__':
    main()
