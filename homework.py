import logging
import os
import time

import requests

import telegram
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKENS')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKENS')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_IDS')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HW_TIME_DEPTH = (60 * 60 * 24 * 30)


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
    """Проверяет существуют ли токены."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])
    #     return PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    # else:
    #     logging.critical('Проверьте токены на наличие!!!!')


def send_message(bot, message):
    """Отправляет сообщение в Telegram."""
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message,        
    )
    

def get_api_answer(timestamp): 
    """Получает API запрос."""   
    response = requests.get(ENDPOINT, headers=HEADERS, params=timestamp)   
    response.json()
    return response


def check_response(response):
    """Проверяет правильность запросов."""
    homework = response["homeworks"]
    return homework[-1]['status']


def parse_status(homework):
    """Показывает результат работы"""
    homework_name = homework['homework_name']
    verdict = homework['verdict']    
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN) 
    timestamp = int(time.time()) - HW_TIME_DEPTH
    
    error_msg = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)            
            verdict = parse_status(response['homeworks'][0])
            send_message(bot, verdict)
        except Exception as error:
            if error_msg != error:
                error_msg = error
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)
            
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
