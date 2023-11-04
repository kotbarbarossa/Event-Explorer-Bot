import asyncio
import os
from datetime import datetime, timedelta
import random
import logging
import re

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (Message,
                           KeyboardButton,
                           ReplyKeyboardMarkup,
                           InlineKeyboardButton,
                           CallbackQuery)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


from get_backend_response import (get_command_response,
                                  get_message_response,
                                  get_location_response,
                                  get_user,
                                  post_user,
                                  get_place_subscription,
                                  get_search_by_name_response,
                                  get_user_subscription)

from get_backend_response import (post_event,
                                  post_event_subscription,
                                  get_place_detail_response,
                                  post_place_subscription,
                                  delete_place_subscription,
                                  post_user_subscription,
                                  delete_user_subscription)

from parsers import parse_element, parse_event

load_dotenv()

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

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

bot = Bot(TELEGRAM_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

BUTTONS = [
    [
        KeyboardButton(text='Места рядом', request_location=True),
        KeyboardButton(text='Поиск но названию')
        ],
    [
        KeyboardButton(text='🌟 Избранное 🌟'),
        KeyboardButton(text='🕺 Подписки 🕺')
        ],
    [KeyboardButton(text='Тыкнуть бота')]
]
reply_markup = ReplyKeyboardMarkup(keyboard=BUTTONS, resize_keyboard=True)


@dp.message(CommandStart())
async def start(message: Message) -> None:
    """Функция инициализации бота."""
    user_id = message.from_user.id
    text = await get_user(user_id)

    if 'error' in text:
        user = message.from_user
        user_id = str(user.id)
        username = user.username if user.username else ''
        first_name = user.first_name if user.first_name else ''
        last_name = user.last_name if user.last_name else ''
        language_code = user.language_code if user.language_code else ''
        is_bot = user.is_bot
        await post_user(
            telegram_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
            is_bot=is_bot)
        text = (
            'Привет! Ты тут в первый раз!\n'
            'Ты так рано, что у нас ещё нет инструкции для тебя!\n'
            'Просто отправь сюда локацию!'
        )

        await message.answer(
            text,
            reply_markup=reply_markup
            )

    else:
        text = 'Рад снова тебя видеть!'
        await message.answer(
            text,
            reply_markup=reply_markup
            )


@dp.message(lambda message: message.location)
async def handle_location(
        message: types.Message,
        **kwargs):
    """Функция обработки сообщений типа 'локация'."""
    user_id = message.from_user.id
    favorite = kwargs.get('favorite')
    search_data = kwargs.get('search_data')

    if favorite:
        response = await get_place_subscription(user_id)
    elif search_data:
        response = await get_search_by_name_response(*search_data.values())
    else:
        latitude = message.location.latitude
        longitude = message.location.longitude
        response = await get_location_response(user_id, latitude, longitude)
    if not response:
        return await message.answer(
            text='Ни чего не найдено 🤷‍♂️',
            reply_markup=reply_markup)
    ELEMENT_LIMIT = 20
    for element in response[:ELEMENT_LIMIT]:
        if element['tags'].get('name'):
            element_id = element['id']
            events = element.get('events')

            text = await parse_element(element)

            button = [
                    [InlineKeyboardButton(
                        text='Смотреть на карте',
                        callback_data=(f'details_button|{element_id}|'
                                       f'{favorite}')
                        )],
                ]

            if events:
                text += f'\n\n<b>Найдено {len(events)} событий:</b>'
                for event in events:
                    text += await parse_event(event=event)

            inline_keyboard = InlineKeyboardBuilder(markup=button)

            await message.answer(
                text=text,
                reply_markup=(inline_keyboard.as_markup())
                )


async def user_favotite_places(message: Message) -> None:
    """Функция выводит избранные места пользователя."""
    await handle_location(message=message, favorite='yes')


async def user_subscriptions(message: types.Message,):
    """Функция отображения подписок пользователя на других пользователей."""
    user_id = message.from_user.id

    users = await get_user_subscription(telegram_id=user_id)

    if not users:
        text = 'У тебя пока нет подписок на пользователей.'
        return await message.answer(
                text=text,)
    for user in users:
        user_telegram_id = user['telegram_id']
        telegram_username = (
            user['telegram_username']
            if user['telegram_username']
            else '-скрыто-@')
        button = [
            [InlineKeyboardButton(
                text="Удалить из избранного",
                callback_data=('delete_subscribe_button|'
                               f'{user_telegram_id}|'
                               f'{telegram_username}'
                               )
                )]
        ]

        inline_keyboard = InlineKeyboardBuilder(markup=button)
        text = f'@{telegram_username}'
        await message.answer(
                text=text,
                reply_markup=inline_keyboard.as_markup(),
                )


@dp.callback_query(lambda query: query.data.startswith('details_button'))
async def details_button(query: CallbackQuery):
    """
    Кнопка "Смотреть на карте" под сообщением с локацией.
    Принимает id локации и параметр favorite.
    При нажатии присылает локацию места и список событий если они есть.
    """
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
            text="Удалить из избранного",
            callback_data=f'delete_favorite_button|{element_id}|{name}'
            )]
    else:
        button = [InlineKeyboardButton(
            text="Добавить место в избранное",
            callback_data=f'add_favorite_button|{element_id}|{name}'
            )]

    await bot.send_message(
        chat_id=chat_id,
        text=text_location,
        )
    buttons = []
    buttons.append(button)

    button = [InlineKeyboardButton(
            text="Пойду сечас (свое событие)",
            callback_data=f'create_fast_event_button|{element_id}'
            )]

    buttons.append(button)

    inline_keyboard = InlineKeyboardBuilder(markup=buttons)

    await bot.send_location(
        chat_id=chat_id,
        latitude=latitude,
        longitude=longitude,
        reply_markup=inline_keyboard.as_markup(),
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
                        text=f'пойду к {event_tg_username} на {event_name}',
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
                            text=f'Подписаться на {event_tg_username}',
                            callback_data=(
                                f'add_subscribe_button|'
                                f'{subscription_id}|'
                                f'{event_tg_username}'
                                )
                            )
                            ]
                buttons.append(subscribe_button)
            inline_keyboard = InlineKeyboardBuilder(markup=buttons)

            await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=inline_keyboard.as_markup(),
                    )

    await bot.send_message(
        chat_id,
        f'Чтобы создать событие с параметрами жми сюда {emoji} '
        f'\n/create_event_{element_id}',
        )


@dp.callback_query(
        lambda query: query.data.startswith('create_fast_event_button'))
async def create_fast_event_button(query: CallbackQuery):
    """
    Кнопка под сообщением с локацией.
    Принимает id локации.
    При нажатии событие создается автоматически.
    """
    chat_id = query.from_user.id

    callback_data_parts = query.data.split("|")

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

    await bot.send_message(
        chat_id,
        'Событие создано!')


@dp.callback_query(lambda query: query.data.startswith('add_favorite_button'))
async def add_favorite_button(query: CallbackQuery):
    """
    Кнопка под сообщением с локацией.
    Принимает id локации и имя локации.
    При нажатии добавляет локацию в избранное.
    """
    chat_id = query.from_user.id

    callback_data_parts = query.data.split("|")

    element_id = callback_data_parts[1]
    element_name = callback_data_parts[2]

    await post_place_subscription(
        telegram_id=str(chat_id), place_id=str(element_id))
    await bot.send_message(
        chat_id, f'{element_name} добавлено в избранное!')


@dp.callback_query(
        lambda query: query.data.startswith('delete_favorite_button'))
async def delete_favorite_button(query: CallbackQuery):
    """
    Кнопка под сообщением с локацией.
    Принимает id локации и имя локации.
    При нажатии удаляет локацию из избранного.
    """
    chat_id = query.from_user.id

    callback_data_parts = query.data.split("|")

    element_id = callback_data_parts[1]
    element_name = callback_data_parts[2]

    await delete_place_subscription(
        telegram_id=str(chat_id), place_id=str(element_id))
    await bot.send_message(
        chat_id, f'{element_name} Удалено из избранного!')


@dp.callback_query(lambda query: query.data.startswith('confirm_parti_button'))
async def confirm_parti_button(query: CallbackQuery):
    """
    Кнопка под сообщением с событием.
    Принимает id и name события.
    При нажатии пользователь подтверждает участие в событии.
    """
    chat_id = str(query.from_user.id)

    callback_data_parts = query.data.split("|")

    event_id = int(callback_data_parts[1])
    event_name = callback_data_parts[2]
    await post_event_subscription(telegram_id=chat_id, event_id=event_id)
    await bot.send_message(
        chat_id,
        f'Участие в {event_name} подтверждено')


@dp.callback_query(
        lambda query: query.data.startswith('delete_subscribe_button'))
async def delete_subscribe_button(query: CallbackQuery):
    """
    Кнопка под сообщением с именем 'пользователь, на которого он подписан'.
    Принимает id обоих пользовтелей.
    При нажатии удаляет подписку на этого пользователя.
    """

    telegram_id = query.from_user.id
    chat_id = query.message.chat.id

    callback_data_parts = query.data.split("|")

    subscription_id = callback_data_parts[1]
    telegram_username = callback_data_parts[2]

    await delete_user_subscription(
        telegram_id=str(telegram_id), subscription_id=str(subscription_id))
    await bot.send_message(
        chat_id=chat_id,
        text=f'Подписка на {telegram_username} удалена!')


@dp.callback_query(lambda query: query.data.startswith('add_subscribe_button'))
async def add_subscribe_button(query: CallbackQuery):
    """
    Кнопка под сообщением с событием.
    Принимает id и name создателя события.
    При нажатии пользователь подписывается на создателя события.
    """
    telegram_id = query.from_user.id

    callback_data_parts = query.data.split("|")

    subscription_id = callback_data_parts[1]
    subscription_username = callback_data_parts[2]
    await post_user_subscription(
        telegram_id=str(telegram_id), subscription_id=str(subscription_id))
    await bot.send_message(
        telegram_id, f'Ты подписался на {subscription_username}!')


class SearchPlaceForm(StatesGroup):
    """Класс состояния для поиска места по названию."""
    place_name = State()
    region_name = State()


@dp.message(lambda message: message.text.startswith('Поиск'))
async def command_start(message: Message, state: FSMContext) -> None:
    """
    Функция запускает переписку с пользователем.
    Пользователь последовательно вводит имя места и регион.
    Последняя функция в цепочке выводит результат поиска по параметрам.
    """

    button = [
        [KeyboardButton(text='Отмена')]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard=button, resize_keyboard=True)

    await state.set_state(SearchPlaceForm.place_name)
    await message.answer(
        (
            'В целях безопасности поиск ограничен в выдаче.'
            '\nВведи название заведения:'
            ),
        reply_markup=reply_markup,
    )


@dp.message(lambda message: message.text.startswith("Отмена"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Отмена переписок с ботом.
    """
    reply_markup = ReplyKeyboardMarkup(keyboard=BUTTONS, resize_keyboard=True)
    logging.info("Cancelling %r")
    await state.clear()
    await message.answer(
        "Ок.",
        reply_markup=reply_markup,
    )


@dp.message(SearchPlaceForm.place_name)
async def process_name(message: Message, state: FSMContext) -> None:
    """Функция принимает и проверяет имя места."""
    text = message.text
    match = re.match(r'^\s*[a-zA-Zа-яА-Я\s]{1,25}\s*$', text)
    if not match:
        await state.set_state(SearchPlaceForm.place_name)
        return await message.answer(
            'Нет такое имя не пойдет!'
            '\nТолько буквы. Не больше 25 символов!'
            '\nПопробуй ещё разок дружок пирожок:')

    await state.update_data(name=message.text)
    await state.set_state(SearchPlaceForm.region_name)
    await message.answer(
        'Введи название региона или города или района:',
    )


@dp.message(SearchPlaceForm.region_name)
async def process_region_name(message: Message, state: FSMContext) -> None:
    """
    Функция принимает и проверяет название региона.
    В случае успеха запускает поиск с заданными параметрами.
    """
    text = message.text
    match = re.match(r'^\s*[a-zA-Zа-яА-Я\s]{1,25}\s*$', text)
    if not match:
        await state.set_state(SearchPlaceForm.region_name)
        return await message.answer(
            'Нет такое имя не пойдет!'
            '\nТолько буквы. Не больше 25 символов!'
            '\nПопробуй ещё разок дружок пирожок:')

    data = await state.update_data(region_name=message.text)
    await state.clear()

    search_data = {
        'chat_id': message.from_user.id,
        'region_name': data["region_name"],
        'place_name': data["name"]
    }
    await message.answer(
                text='Производится поиск. Не вытаскивайте дискету с данными.',
                reply_markup=reply_markup)
    return await handle_location(message, search_data=search_data)


class EventCreationForm(StatesGroup):
    """Класс состояния для создания события с параметрами."""
    event_name = State()
    event_description = State()
    event_date = State()
    event_time = State()
    event_duration = State()


async def is_valid_date(date_str):
    """Функция валидации даты события."""
    try:
        datetime.strptime(date_str, '%d-%m-%Y')
        return True
    except ValueError:
        return False


async def is_valid_time(time_str):
    """Функция валидации времени события."""
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False


@dp.message(lambda message: message.text.startswith('/create_event_'))
async def create_event_start(message: Message, state: FSMContext) -> None:
    """
    Функция запускает переписку с пользователем.
    Пользователь последовательно вводит параметры события.
    Последняя функция в цепочке создает событие.
    """
    message_text = message.text
    match = re.match(r'^/create_event_(\d+)', message_text)
    if match:

        place_id = match.group(1)
        await state.update_data(place_id=place_id)
        await state.update_data(chat_id=str(message.from_user.id))

        button = [
            [KeyboardButton(text='Отмена')]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard=button, resize_keyboard=True)

        await state.set_state(EventCreationForm.event_name)
        await message.answer(
            (
                'Введи название события:'),
            reply_markup=reply_markup,
        )
    else:
        await message.answer(
            'Неверный формат команды. '
            'Используй /create_event_<place_id>')


@dp.message(EventCreationForm.event_name)
async def create_event_name(message: Message, state: FSMContext) -> None:
    """Функция принимает и проверяет имя события."""
    event_name = message.text
    match = re.match(r'^\s*[a-zA-Zа-яА-Я\s]{1,25}\s*$', event_name)
    if not match:
        await state.set_state(EventCreationForm.event_name)
        return await message.answer(
            'Нет такое имя не пойдет!'
            '\nТолько буквы. Не больше 25 символов!'
            '\nПопробуй ещё разок дружок пирожок:')

    await state.update_data(event_name=event_name)
    await state.set_state(EventCreationForm.event_description)
    await message.answer(
        'Введи описание события:',
    )


@dp.message(EventCreationForm.event_description)
async def create_event_description(
        message: Message, state: FSMContext) -> None:
    """Функция принимает и проверяет описание события."""
    event_description = message.text
    match = re.match(r'^\s*[a-zA-Zа-яА-Я\s]{1,25}\s*$', event_description)
    if not match:
        await state.set_state(EventCreationForm.event_description)
        return await message.answer(
            'Нет такое имя не пойдет!'
            '\nТолько буквы. Не больше 25 символов!'
            '\nПопробуй ещё разок дружок пирожок:')

    await state.update_data(event_description=event_description)
    await state.set_state(EventCreationForm.event_date)
    await message.answer(
        'Введи дату события (дд-мм-гггг):',
    )


@dp.message(EventCreationForm.event_date)
async def create_event_date(message: Message, state: FSMContext) -> None:
    """Функция принимает и проверяет дату события."""
    event_date = message.text
    if not await is_valid_date(event_date):
        return await message.answer(
            'Нет такая дата не пойдет!'
            '\nТолько такой формат -> дд-мм-гггг!'
            '\nПопробуй ещё разок дружок пирожок:')

    await state.update_data(event_date=event_date)
    await state.set_state(EventCreationForm.event_time)
    await message.answer(
        'Введи время начала (чч:мм):',
        )


@dp.message(EventCreationForm.event_time)
async def create_event_time(message: Message, state: FSMContext) -> None:
    """Функция принимает и проверяет время начала события."""
    event_time = message.text
    if not await is_valid_time(event_time):
        return await message.answer(
            'Нет такое время не пойдет!'
            '\nТолько такой формат -> чч:мм!'
            '\nПопробуй ещё разок дружок пирожок:')

    await state.update_data(event_time=event_time)
    await state.set_state(EventCreationForm.event_duration)
    await message.answer(
        'Введи длительность в часах:',
        )


@dp.message(EventCreationForm.event_duration)
async def create_event_duration(message: Message, state: FSMContext) -> None:
    """
    Функция принимает и проверяет длительность события.
    В случе успеха создает событие по заданным параметрам.
    """
    event_duration = message.text
    try:
        event_duration = int(event_duration)
        if 0 < event_duration <= 12:
            pass
        else:
            return await message.answer(
                'Так не пойдет!'
                '\nОт 1 до 12 часов!'
                '\nПопробуй ещё разок дружок пирожок:')
    except ValueError:
        return await message.answer(
            'Никуда не годится!'
            '\nТолько число от 1 до 12!'
            '\nПопробуй ещё разок дружок пирожок:')

    event = await state.update_data(event_duration=event_duration)
    await state.clear()

    date_str = f'{event["event_date"]} {event["event_time"]}:00.123000'
    start_datetime = datetime.strptime(date_str, '%d-%m-%Y %H:%M:%S.%f')

    end_datetime = start_datetime + timedelta(hours=event_duration)
    event['start_datetime'] = start_datetime.isoformat()
    event['end_datetime'] = end_datetime.isoformat()

    await post_event(
        name=event['event_name'],
        description=event['event_description'],
        telegram_id=event['chat_id'],
        place_id=event['place_id'],
        start_datetime=event['start_datetime'],
        end_datetime=event['end_datetime']
        )

    await message.answer(
                text='Событие создано!',
                reply_markup=reply_markup)


@dp.message()
async def handle_message(message: types.Message) -> None:
    """Функция обработки неизвестных боту сообщений."""
    user_id = message.from_user.id
    user_message = message.text

    button_messages = {
        '🌟 Избранное 🌟': user_favotite_places,
        'Тыкнуть бота': start,
        '🕺 Подписки 🕺': user_subscriptions,
    }
    if user_message not in button_messages:
        text = await get_message_response(user_message, user_id)
        await message.answer(
            text,
            reply_markup=reply_markup
            )
    else:
        await button_messages[user_message](message=message)


@dp.message(lambda message: message.text.startswith('/'))
async def handle_command(message: Message) -> None:
    """Функция обработки неизвестных боту команд."""
    command = message.text.replace('/', '')
    chat_id = message.from_user.id
    text = await get_command_response(command, chat_id)
    await bot.send_message(chat_id=message.from_user.id, text=text)


async def main() -> None:
    """Основная логика работы бота."""

    await dp.start_polling(bot)


if __name__ == '__main__':

    logging.basicConfig(
        filename='Event_Explorer.log',
        format='%(asctime)s - %(name)s - %(levelname)s - LINE: %(lineno)d'
        ' - FUNCTION: %(funcName)s - MESSAGE: %(message)s',
        level=logging.INFO,
        filemode='w'
    )

    asyncio.run(main())
