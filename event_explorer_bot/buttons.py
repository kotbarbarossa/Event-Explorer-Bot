from datetime import datetime, timedelta
import random

from telegram import (Update, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler

from get_backend_response import (post_event,
                                  post_event_subscription,
                                  get_place_detail_response,
                                  post_place_subscription,
                                  delete_place_subscription,
                                  post_user_subscription,
                                  delete_user_subscription)

from parsers import parse_event

EVENTS_NAMES = [
    "Шоколадный дождь",
    "Пылесос для животных",
    "Танцующий брокколи",
    "Мороженое с женым",
    "Кот в шляпе",
    "Спящий бульдог",
    "Ракета-тостер",
    "Слон в пижаме",
    "Змея-акробат",
    "Грозный пушистик",
    "Пингвин-гитарист",
    "Блудившийся ананас",
    "Веселый огурчик",
    "Летающая капуста",
    "Хоровой единорог",
    "Колдующий крокодил",
    "Морской единорог",
    "Шарик-воздушный шар",
    "Смешанный омлет",
    "Робот-подсолнух"
]


async def details_button(update: Update, context: CallbackContext):
    """
    Кнопка "Смотреть на карте" под сообщением с локацией.
    Принимает id локации и параметр favorite.
    При нажатии присылает локацию места и список событий если они есть.
    """
    query = update.callback_query
    chat_id = query.from_user.id
    callback_data = query.data.split('|')
    element_id = callback_data[1]
    favorite = callback_data[2]
    emoji = "⬇"

    place_detail = await get_place_detail_response(
        telegram_id=chat_id, place_id=element_id)
    latitude = place_detail['lat']
    longitude = place_detail['lon']
    name = place_detail['tags']['name']
    events = place_detail.get('events')

    text_location = ('Чтобы узнать маршрут'
                     f'\nдо <b>{name}</b>'
                     f'\nнажми на карту {emoji}.')

    if favorite == 'yes':
        button = [InlineKeyboardButton(
            "Удалить из избранного",
            callback_data=f'delete_favorite_button|{element_id}|{name}'
            )]
    else:
        button = [InlineKeyboardButton(
            "Добавить место в избранное",
            callback_data=f'add_favorite_button|{element_id}|{name}'
            )]

    await context.bot.send_message(
        chat_id=chat_id,
        text=text_location,
        parse_mode=ParseMode.HTML)

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(
                "Пойду сечас (свое событие)",
                callback_data=f'create_fast_event_button|{element_id}'
                )],
            button,
        ]
    )
    await context.bot.send_location(
        chat_id=chat_id,
        latitude=latitude,
        longitude=longitude,
        reply_markup=keyboard,
        )

    if events:
        for event in events:
            text = ''
            subscription_id = event.get('user_id')
            subscription_username = event.get('telegram_username')
            event_id = event.get('id')
            event_name = event.get('name')
            if event.get('telegram_username'):
                event_tg_username = (
                    f'@{event.get("telegram_username")}')
            else:
                event_tg_username = 'Безымянный Джо'

            text += await parse_event(event=event)

            buttons = []
            event_button = [InlineKeyboardButton(
                        f'пойду к {event_tg_username} на {event_name}',
                        callback_data=(
                            f'confirm_parti_button|'
                            f'{event_id}|'
                            f'{event_name}'
                            )
                        )
                        ]
            buttons.append(event_button)
            if subscription_username:
                subscribe_button = [InlineKeyboardButton(
                            f'Подписаться на {event_tg_username}',
                            callback_data=(
                                f'add_subscribe_button|'
                                f'{subscription_id}|'
                                f'{event_tg_username}'
                                )
                            )
                            ]
                buttons.append(subscribe_button)
            keyboard = InlineKeyboardMarkup(buttons)

            await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                    )

    await context.bot.send_message(
        chat_id,
        f'Чтобы создать событие с параметрами жми сюда {emoji} '
        f'\n/create_event_{element_id}',
        )


async def create_fast_event_button(update: Update, context: CallbackContext):
    """
    Кнопка под сообщением с локацией.
    Принимает id локации.
    При нажатии событие создается автоматически.
    """
    query = update.callback_query
    chat_id = query.from_user.id

    callback_data_parts = update.callback_query.data.split("|")

    element_id = callback_data_parts[1]

    start_datetime = datetime.now()
    end_datetime = start_datetime + timedelta(hours=3)

    random_name = random.choice(EVENTS_NAMES)

    await post_event(
        name=random_name,
        description='',
        telegram_id=str(chat_id),
        place_id=element_id,
        start_datetime=start_datetime.isoformat(),
        end_datetime=end_datetime.isoformat())

    await context.bot.send_message(
        chat_id,
        'Событие создано!')


async def add_favorite_button(update: Update, context: CallbackContext):
    """
    Кнопка под сообщением с локацией.
    Принимает id локации и имя локации.
    При нажатии добавляет локацию в избранное.
    """
    query = update.callback_query
    chat_id = query.from_user.id

    callback_data_parts = update.callback_query.data.split("|")

    element_id = callback_data_parts[1]
    element_name = callback_data_parts[2]

    await post_place_subscription(
        telegram_id=str(chat_id), place_id=str(element_id))
    await context.bot.send_message(
        chat_id, f'{element_name} добавлено в избранное!')


async def delete_favorite_button(update: Update, context: CallbackContext):
    """
    Кнопка под сообщением с локацией.
    Принимает id локации и имя локации.
    При нажатии удаляет локацию из избранного.
    """
    query = update.callback_query
    chat_id = query.from_user.id

    callback_data_parts = update.callback_query.data.split("|")

    element_id = callback_data_parts[1]
    element_name = callback_data_parts[2]

    await delete_place_subscription(
        telegram_id=str(chat_id), place_id=str(element_id))
    await context.bot.send_message(
        chat_id, f'{element_name} Удалено из избранного!')


async def confirm_parti_button(update: Update, context: CallbackContext):
    """
    Кнопка под сообщением с событием.
    Принимает id и name события.
    При нажатии пользователь подтверждает участие в событии.
    """
    query = update.callback_query
    chat_id = str(query.from_user.id)

    callback_data_parts = update.callback_query.data.split("|")

    event_id = int(callback_data_parts[1])
    event_name = callback_data_parts[2]
    await post_event_subscription(telegram_id=chat_id, event_id=event_id)
    await context.bot.send_message(
        chat_id,
        f'Участие в {event_name} подтверждено')


async def delete_subscribe_button(update: Update, context: CallbackContext):
    """
    Кнопка под сообщением с именем 'пользователь, на которого он подписан'.
    Принимает id обоих пользовтелей.
    При нажатии удаляет подписку на этого пользователя.
    """
    query = update.callback_query
    telegram_id = query.from_user.id

    callback_data_parts = update.callback_query.data.split("|")

    subscription_id = callback_data_parts[1]
    telegram_username = callback_data_parts[2]

    await delete_user_subscription(
        telegram_id=str(telegram_id), subscription_id=str(subscription_id))
    await context.bot.send_message(
        telegram_id, f'Подписка на {telegram_username} удалена!')


async def add_subscribe_button(update: Update, context: CallbackContext):
    """
    Кнопка под сообщением с событием.
    Принимает id и name создателя события.
    При нажатии пользователь подписывается на создателя события.
    """
    query = update.callback_query
    telegram_id = query.from_user.id

    callback_data_parts = update.callback_query.data.split("|")

    subscription_id = callback_data_parts[1]
    subscription_username = callback_data_parts[2]
    await post_user_subscription(
        telegram_id=str(telegram_id), subscription_id=str(subscription_id))
    await context.bot.send_message(
        telegram_id, f'Ты подписался на {subscription_username}!')


buttons_handlers = [
    CallbackQueryHandler(
        details_button, pattern="details_button"),
    CallbackQueryHandler(
        create_fast_event_button, pattern="create_fast_event_button"),
    CallbackQueryHandler(
        add_favorite_button, pattern="add_favorite_button"),
    CallbackQueryHandler(
        confirm_parti_button, pattern="confirm_parti_button"),
    CallbackQueryHandler(
        delete_favorite_button, pattern="delete_favorite_button"),
    CallbackQueryHandler(
        delete_subscribe_button, pattern="delete_subscribe_button"),
    CallbackQueryHandler(
        add_subscribe_button, pattern="add_subscribe_button"),
]
