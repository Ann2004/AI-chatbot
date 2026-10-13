import logging
import os
import random

from dotenv import load_dotenv
from google.cloud import dialogflow
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType


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

    return response.query_result


def send_message(event, vk_api, message):
    """Send a message to the user."""

    vk_api.messages.send(
        user_id=event.user_id,
        message=message,
        random_id=random.randint(1, 1000),
    )


def main() -> None:
    load_dotenv()
    vk_token = os.environ['VK_TOKEN']
    project_id = os.environ['DIALOGFLOW_PROJECT_ID']

    vk_session = vk.VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            query_result = detect_intent_text(
                project_id=project_id,
                session_id=event.user_id,
                text=event.text,
            )

            if query_result.intent.is_fallback:
                continue
            
            send_message(event, vk_api, query_result.fulfillment_text)


if __name__ == '__main__':
    main()
