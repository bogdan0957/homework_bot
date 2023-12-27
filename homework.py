import logging
import os
import sys
import time
import requests

import telegram
from dotenv import load_dotenv
from exceptions import GetApiAnswerError, ParseStatusError
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


def check_tokens() -> bool:
    """.
    Функция chech_tokens проверяет наличие
    токенов для работы телеграм бота.
    """
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


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
    request_dict = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {
            'from_date': timestamp
        }
    }
    try:
        response = requests.get(request_dict)
        if response.status_code != HTTPStatus.OK:
            raise GetApiAnswerError(
                f'Недоступность эндпоинта к URL {ENDPOINT},'
                f'с параметрами в виде промежутка времени {timestamp}'
                f'и с ошибкой в виде не соответствия статус кода'
                f'запроса с HTTPStatus.OK')
        return response.json()
    except requests.RequestException:
        raise ConnectionError(
            f'Сбой запроса к API {ENDPOINT}'
            f'с параметрами в виде промежутка времени {timestamp}.'
            f'Нет возможности получить ответ API в ввиде словаря')


def check_response(response):
    """.
    Функция check_response возвращает статус
    последней выполненной домашней работы.
    """
    if 'homeworks' not in response:
        raise KeyError('В ответе API нет ключа homeworks')
    homework = response['homeworks']
    if not isinstance(homework, list):
        raise TypeError('Ключ homeworks пришел не в виде списка')
    if not homework:
        raise KeyError('Список homework пуст')
    if not homework[0]['status']:
        raise KeyError('Нет ключа статус')
    status = homework[0]['status']
    return status


def parse_status(homework):
    """.
    Функция parse_status возвращает homework_name.
    и verdict, полученный из списка homeworks.
    """
    if 'homework_name' not in homework:
        raise KeyError('В ответе API нет ключа с названием homework_name')
    if not homework['status']:
        raise KeyError('Нет ключа статус')
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ParseStatusError('Статус домашней работы недокументированный')
    verdict = HOMEWORK_VERDICTS[status]
    homework_name = homework['homework_name']
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('НЕТ ТОКЕНА(ТОКЕНОВ)')
        sys.exit('Проверьте токены, затем перезапустите бота')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homework = response.get('homeworks')[0]
            message = parse_status(homework)
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
