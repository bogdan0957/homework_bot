import logging
import os
import sys
import time
import requests

import telegram
from dotenv import load_dotenv
from exceptions import CheckResponseError, GetApiAnswerError, ParseStatusError
from http import HTTPStatus

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKENS')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKENS')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_IDS')

RETRY_PERIOD = 600

ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('homework.log'),
        logging.StreamHandler(),
    ]
)


def check_tokens():
    """.
    Функция chech_tokens проверяет наличие
    токенов для работы телеграм бота.
    """
    try:
        if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID is not None:
            return PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    except CheckResponseError:
        logging.critical('НЕ ХВАТАЕТ ТОКЕНОВ, ТЕЛЕГРАМ БОТ НЕ БУДЕТ РАБОТАТЬ')


def send_message(bot, message):
    """.
    Функция send_message отправляет сообщение в телеграм чат,
    который привязан к переменной chat_id.
    """
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug('Удачная отправка сообщения пользователю')
    except telegram.error.TelegramError as error:
        logging.error(f'Ошибка отправки сообщения пользователю {error}')


def get_api_answer(timestamp):
    """.
    Функция get_api_answer делает запрос api к ENDPOINT
    Яндекс.Практикума и возвращает api запрос в виде словаря.
    """
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS,
                                params={'from_date': timestamp})
        if response.status_code != HTTPStatus.OK:
            raise GetApiAnswerError('Недоступность эндпоинта')
        return response.json()
    except requests.RequestException:
        logging.error('Сбой запроса к API')


def check_response(response):
    """.
    Функция check_response возвращает статус
    последней выполненной домашней работы.
    """
    if 'homeworks' not in response:
        raise TypeError('В ответе API нет ключа homeworks')
    homework = response['homeworks']
    if not isinstance(homework, list):
        raise TypeError('Ключ homeworks пришел не в виде списка')
    status = homework[0]['status']
    return status


def parse_status(homework):
    """.
    Функция parse_status возвращает homework_name.
    и verdict, полученный из списка homeworks.
    """
    if "homework_name" not in homework:
        raise KeyError('В ответе API нет ключа с названием homework_name')
    status = homework['status']
    if status == 'unknown':
        raise ParseStatusError('Статус домашней работы недокументированный')
    verdict = HOMEWORK_VERDICTS[status]
    homework_name = homework['homework_name']
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    if not check_tokens():
        logging.critical('НЕТ ТОКЕНА(ТОКЕНОВ)')
        sys.exit('')

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homework = response.get('homeworks')[0]
            message = parse_status(homework)
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
