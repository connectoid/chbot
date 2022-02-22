import json
import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telegram import Bot, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from exceptions import WrongEndpointException

load_dotenv()


WEATHER_API = os.getenv('WEATHER_API')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

ENDPOINT = 'http://api.weatherapi.com/v1/current.json'

RETRY_TIME = 600

WEATHER_KEYS = {
    'temp_c': 'Температура, С',
    'feelslike_c': 'Ощущается, С',
    'wind_kph': 'Ветер, м/с',
    'gust_kph': 'Порывы, м/с',
    'cloud': 'Облачность, %',
    'condition': 'Явления',
    'wind_dir': 'Направление ветра',
    'wind_degree': 'Направление ветра, гр',
    'precip_mm': 'Осадки, мм/ч',
    'vis_km': 'Видимость, км',
    'pressure_mb': 'Давление, мБ',
    'humidity': 'Влажность, %',
}

TOKENS = ('WEATHER_API', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')


bot = Bot(token=TELEGRAM_TOKEN)

updater = Updater(token='5288168645:AAE8HpNnM99UMyk-GVlhDGxvu7LGfqOksWQ')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
)
handler.setFormatter(formatter)


def log_and_raise(exception, msg):
    """Логирование и поднятие исключения."""
    logger.error(msg)
    raise exception(msg)


def wind_translate(wind):
    replaced_letters = {'W': 'З', 'E': 'В', 'S': 'Ю', 'N': 'С'}
    for i, j in replaced_letters.items():
        wind = wind.replace(i, j)
    return wind


def kmh_in_ms(speed):
    speed_ms = speed * 1000 / 3600
    return round(speed_ms, 1)


def print_weather(parsed_weather):
    for key, value in parsed_weather.items():
        print(key, ':', value)


def prepare_weather_for_post(parsed_weather):
    weather_list = []
    for key, value in parsed_weather.items(): 
        weather_list.append(str(key) + ': ' + str(value))
    weather_string = '\n'.join(weather_list)
    return weather_string


def check_tokens():
    """Проверяет доступность переменных окружения."""
    check = True
    for token in TOKENS:
        if not globals()[token]:
            logger.critical(f'Отсутсвует обязательная переменная {token}')
            check = False
    return check


def get_weather_api(city):
    """Отправляет запрос к эндпоинту и проверяет ответа.
    Возвращает JSON ответ приведенный к типам Python.
    """
    aqi = 'no'
    lang = 'ru'
    params = {'key': WEATHER_API, 'q': city, 'aqi': aqi, 'lang': lang}
    try:
        response = requests.get(ENDPOINT, params)
    except requests.ConnectionError as error:
        logger.error(f'Cбой при обращении к URL: {error}')
    else:
        if response.status_code != HTTPStatus.OK:
            log_and_raise(WrongEndpointException, 'Недоступен эндпоинт')
        else:
            try:
                return response.json()
            except json.decoder.JSONDecodeError as error:
                logger.error(
                    f'Cбой при преобразовании ответа в JSONL: {error}'
                )


def parse_weather(weather):
    """Парсинг погоды из JSON"""
    current_weather = {}
    try:
        for key, value in WEATHER_KEYS.items():
            if key == 'condition':
                current_weather.update(
                    {value: weather['current'][key]['text']}
                    )
            elif key in ('wind_kph', 'gust_kph'): 
                current_weather.update(
                    {value: kmh_in_ms(weather['current'][key])}
                    )
            elif key == 'wind_dir':
                current_weather.update(
                    {value: wind_translate(weather['current'][key])}
                    )
            else:
                current_weather.update({value: weather['current'][key]})
    except KeyError as error:
        log_and_raise(KeyError, f'Отсутствие ключа в словаре: {error}')
    else:
        return current_weather


def post_weather(update, context):
    chat = update.effective_chat
    city = update.message.text
    context.bot.send_message(
        chat_id=chat.id, text=f'В настоящий момент погода в {city} такая:'
        )
    weather = get_weather_api(city)
    parsed_weather = parse_weather(weather)
    print('* * * * * *', city, '* * * * * *')
    print_weather(parsed_weather)
    weather_for_post = prepare_weather_for_post(parsed_weather)
    context.bot.send_message(chat_id=chat.id, text=weather_for_post)


def wake_up(update, context):
    chat = update.effective_chat
    name = update.message.chat.first_name
    buttons = ReplyKeyboardMarkup([
                ['Провидения', 'Анадырь', 'Уголльные копи'],
                ['Эгвекинот', 'Лаврентия', 'Мыс Шмидта'],
                ['Певек', 'Билибино', 'Беринговский']
            ])
    context.bot.send_message(
        chat_id=chat.id,
        text='Спасибо, что включили меня, {}!'.format(name),
        reply_markup=buttons
        )


def main():
    updater.dispatcher.add_handler(CommandHandler('start', wake_up))

    updater.dispatcher.add_handler(MessageHandler(Filters.text, post_weather))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
