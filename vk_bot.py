import logging
import os

from dotenv import load_dotenv
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)


logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    load_dotenv()
    vk_token = os.environ['VK_TOKEN']

    vk_session = vk_api.VkApi(token=vk_token)

    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            print('Новое сообщение:')
            if event.to_me:
                print('Для меня от:', event.user_id)
            else:
                print('От меня для:', event.user_id)
            print('Текст:', event.text)


if __name__ == '__main__':
    main()
