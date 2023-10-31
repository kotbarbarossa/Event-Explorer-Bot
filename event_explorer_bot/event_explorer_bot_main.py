import os
from dotenv import load_dotenv
import logging
import re
from datetime import datetime, timedelta
import random

from telegram import (Update, InlineKeyboardMarkup, InlineKeyboardButton,
                      ReplyKeyboardMarkup)
from telegram.constants import ParseMode
from telegram.ext import (filters, MessageHandler, ApplicationBuilder,
                          CommandHandler, ContextTypes, CallbackContext,
                          CallbackQueryHandler, ConversationHandler,)

from get_backend_response import (get_command_response,
                                  get_message_response,
                                  get_location_response,
                                  get_user,
                                  post_user,
                                  post_event,
                                  get_place_subscription,
                                  get_search_by_name_response,
                                  get_user_subscription)

from buttons import (details_button,
                     create_fast_event_button,
                     add_favorite_button,
                     confirm_parti_button,
                     delete_favorite_button,
                     add_subscribe_button,
                     delete_subscribe_button)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

EMOJI_LIST = ['😄', '🎉', '🥳', '🎈', '🌟', '🎁', '🎂', '🍾', '🎊', '🥂',
              '🤩', '🍰', '🎆', '🎇', '🎗️', '🎀', '🧨', '🪅', '🎵', '🎷',
              '🎸', '🎶', '🍸', '🍹', '🍻', '🕺', '💃', '🕶️', '📸', '🌈']


EMOJI_PROFESSIONS_LIST = ['👮', '🕵️', '👷', '👩‍🚒', '👨‍🌾', '👩‍🍳', '👨‍🎓',
                          '👩‍🏫', '👨‍🎤', '👩‍🎨', '👨‍🚀', '👩‍⚖️', '👨‍🦼', '👩‍🦯',
                          '🧕', '🧙‍♂️', '🧛‍♀️', '🧝‍♂️', '🧞‍♀️', '🧜‍♂️', '🦸‍♀️',
                          '🦹‍♂️', '🦺', '🤴', '👸', '🎅', '🧑‍🎓', '🧑‍🏫',
                          '🧑‍🎤', '🧑‍🎨', '🧑‍🚀', '🧑‍⚖️', '🧑‍🦼', '🧑‍🦯', '🦰',
                          '🦱', '🦳', '🦲', '👩‍⚕️', '👨‍⚕️', '👩‍🔬', '👨‍🔬',
                          '👩‍💼', '👨‍💼', '👩‍🌾', '👨‍🌾', '👩‍🍳', '👨‍🍳', '👩‍🎤',
                          '👨‍🎤', '👩‍🎨', '👨‍🎨', '👩‍🚀', '👨‍🚀', '👩‍⚖️', '👨‍⚖️',
                          '👩‍🦯', '👨‍🦯', '🦫', '🦭', '🐈‍⬛', '🦮', '🦙',
                          '🦥', '🦦', '🦨', '🦩']

[
    EVENT_NAME,
    EVENT_DESCRIPTION,
    EVENT_DATE,
    EVENT_TIME,
    EVENT_DURATION
] = range(5)

SEARCH_NAME, SEARCH_REGION_NAME = range(2)

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

BUTTONS = [
    ['🌟 Избранное 🌟', '🕺 Подписки 🕺'],
    ['Поиск'],
    ['Тыкнуть бота']
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция инициализации бота."""
    chat_id = update.message.chat_id
    text = await get_user(chat_id)
    reply_markup = ReplyKeyboardMarkup(BUTTONS, resize_keyboard=True)

    if 'error' in text:
        user = update.message.from_user
        user_id = str(user.id)
        username = user.username if hasattr(user, 'username') else ''
        first_name = user.first_name if hasattr(user, 'first_name') else ''
        last_name = user.last_name if hasattr(user, 'last_name') else ''
        language_code = user.language_code if hasattr(
            user, 'language_code') else ''
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
            'Ты так рано что у нас ещё нет инструкции для тебя!\n'
            'Сорян придется тыкать пальчиками самому!'
                )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup
            )
    else:
        text = 'Рад снова тебя видеть!'
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=reply_markup
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция обработки неизвестных боту сообщений."""
    chat_id = update.message.chat_id
    message = update.message.text

    messages = {
        '🌟 Избранное 🌟': user_favotite_places,
        'Тыкнуть бота': start,
    }
    if message not in messages:
        text = await get_message_response(message, chat_id)
        await context.bot.send_message(chat_id=chat_id, text=text)
    else:
        await messages[message](update, context)


async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция обработки неизвестных боту команд."""
    command = update.message.text.replace('/', '')
    chat_id = update.effective_chat.id
    text = await get_command_response(command, chat_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def parse_element(element) -> str:
    text = ''
    amenity = element['tags'].get('amenity')
    name = element['tags'].get(
        'name') or element['tags'].get('name:en')
    name_ru = element['tags'].get('name:ru')
    opening_hours = element['tags'].get('opening_hours')
    cuisine = element['tags'].get('cuisine')
    outdoor_seating = element['tags'].get('outdoor_seating')
    website = element['tags'].get('website')
    website_menu = element['tags'].get('website:menu')
    contact_vk = element['tags'].get('contact:vk')
    contact_website = element['tags'].get('contact:website')

    text = f'<b>{name}</b>'

    if amenity:
        text += f' <i>{amenity}</i>'
    if name_ru:
        text += f'\n{name_ru}'
    if opening_hours:
        text += f'\nВремя работы: {opening_hours}'
    if cuisine:
        text += f'\nКухня: {cuisine.replace(";", ", ")}'
    if outdoor_seating == 'yes':
        text += '\nЕсть терасса'
    if website:
        text += f'\n{website}'
    if website_menu:
        text += f'\nМеню: {website_menu}'
    if contact_vk:
        text += f'\nVK: {contact_vk}'
    if contact_website:
        text += f'\n{contact_website}'
    return text


async def parse_event(event) -> str:
    text = ''

    time_obj_start = datetime.fromisoformat(
        event.get('start_datetime'))
    time_obj_end = datetime.fromisoformat(
        event.get('end_datetime'))
    event_wnen = time_obj_start.strftime('%d/%m/%Y')
    event_name = event.get('name')
    event_description = event.get('description')
    if event.get('telegram_username'):
        event_tg_username = (
            f'@{event.get("telegram_username")}')
    else:
        event_tg_username = 'Безымянный Джо'
    event_start = time_obj_start.strftime('%H:%M')
    event_end = time_obj_end.strftime('%H:%M')
    event_participants = event.get('event_participants')
    emoji_one = random.choice(EMOJI_LIST)
    emoji_two = random.choice(EMOJI_LIST)
    emoji_three = random.choice(EMOJI_LIST)
    text += f'\n{emoji_one}{emoji_two}{emoji_three}'
    text += f'\nКогда: {event_wnen}'
    text += f'\nНазвание: {event_name}'
    if event_description:
        text += f'\nОписание: {event_description}'
    text += f'\nОрганизует: {event_tg_username}'
    text += f'\nНачало: {event_start}'
    text += f'\nКонец: {event_end}'
    if event_participants:
        text += '\nУчастники: '
        for user in event_participants:
            if user.get('telegram_username'):
                tg_username = (
                    f'@{user.get("telegram_username")}')
            else:
                tg_username = 'Безымянный Джо'
            text += f'\n{random.choice(EMOJI_LIST)} '
            text += f'{tg_username}'
    text += '\n'
    return text


async def handle_location(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE, **kwargs):
    """Функция обработки сообщений типа 'локация'."""
    chat_id = update.effective_chat.id
    favorite = kwargs.get('favorite')
    search_data = kwargs.get('search_data')

    if favorite:
        response = await get_place_subscription(chat_id)
    elif search_data:
        response = await get_search_by_name_response(*search_data.values())
    else:
        latitude = update.message.location.latitude
        longitude = update.message.location.longitude
        response = await get_location_response(chat_id, latitude, longitude)
    if not response:
        return await context.bot.send_message(
            chat_id,
            'Ни чего не найдено 🤷‍♂️')
    ELEMENT_LIMIT = 20
    for element in response[:ELEMENT_LIMIT]:
        if element['tags'].get('name'):
            element_id = element['id']
            events = element.get('events')

            text = await parse_element(element)

            buttons = [
                    [InlineKeyboardButton(
                        'Смотреть на карте',
                        callback_data=(f'details_button|{element_id}|'
                                       f'{favorite}')
                        )],
                ]

            if events:
                text += f'\n\n<b>Найдено {len(events)} событий:</b>'
                for event in events:
                    text += await parse_event(event=event)

            keyboard = InlineKeyboardMarkup(buttons)

            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
                )


async def user_favotite_places(
        update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция выводит избранные места пользователя."""
    await handle_location(update, context, favorite='yes')


async def user_subscriptions(
        update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция отображения подписок пользователя на других пользователей."""
    chat_id = update.message.chat_id

    users = await get_user_subscription(telegram_id=chat_id)

    if not users:
        text = 'У вас пока нет подписок на пользователей'
        return await context.bot.send_message(chat_id, text)
    for user in users:
        user_telegram_id = user['telegram_id']
        telegram_username = user['telegram_username']
        button = [InlineKeyboardButton(
            "Удалить из избранного",
            callback_data=('delete_subscribe_button|'
                           f'{user_telegram_id}|'
                           f'{telegram_username}')
            )]
        keyboard = InlineKeyboardMarkup([button])
        text = f'@{telegram_username}'
        return await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    )


async def create_event(update: Update, context: CallbackContext):
    """
    Функция запускает переписку с пользователем.
    Пользователь последовательно вводит параметры события.
    Последняя функция в цепочке создает событие.
    """
    message_text = update.message.text
    match = re.match(r'^/create_event_(\d+)', message_text)

    if match:
        place_id = match.group(1)
        context.user_data['event'] = {}
        context.user_data['event']['place_id'] = place_id
        context.user_data['event']['chat_id'] = str(
            update.message.from_user.id)

        await update.message.reply_text('Введи название события:')
        return EVENT_NAME
    else:
        await update.message.reply_text(
            'Неверный формат команды. '
            'Используйте /create_event_<place_id>')
        return ConversationHandler.END


async def get_event_name(update: Update, context: CallbackContext):
    """Функция принимает и проверяет имя события."""
    text = update.message.text
    match = re.match(r'^\s*[a-zA-Zа-яА-Я\s]{1,25}\s*$', text)
    if not match:
        await update.message.reply_text(
            'Нет такое имя не пойдет!'
            '\nТолько буквы. Не больше 25 символов!'
            '\nПопробуй ещё разок дружок пирожок:')
        return EVENT_NAME
    context.user_data['event']['name'] = text
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, 'Введи описание события:')
    return EVENT_DESCRIPTION


async def get_event_description(update: Update, context: CallbackContext):
    """Функция принимает и проверяет описание события."""
    text = update.message.text
    match = re.match(r'^\s*[a-zA-Zа-яА-Я\s]{1,25}\s*$', text)
    if not match:
        await update.message.reply_text(
            'Нет такое описание не пойдет!'
            '\nТолько буквы. Не больше 25 символов!'
            '\nПопробуй ещё разок дружок пирожок:')
        return EVENT_DESCRIPTION
    context.user_data['event']['description'] = text
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, 'Введи дату события (дд-мм-гггг):')
    return EVENT_DATE


async def is_valid_date(date_str):
    """Функция валидации даты события."""
    try:
        datetime.strptime(date_str, '%d-%m-%Y')
        return True
    except ValueError:
        return False


async def get_event_date(update: Update, context: CallbackContext):
    """Функция принимает и проверяет дату события."""
    text = update.message.text
    if not await is_valid_date(text):
        await update.message.reply_text(
            'Нет такая дата не пойдет!'
            '\nТолько такой формат -> дд-мм-гггг!'
            '\nПопробуй ещё разок дружок пирожок:')
        return EVENT_DATE
    context.user_data['event']['date'] = text
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, 'Введи время начала (чч:мм):')
    return EVENT_TIME


async def is_valid_time(time_str):
    """Функция валидации времени события."""
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False


async def get_event_time(update: Update, context: CallbackContext):
    """Функция принимает и проверяет время начала события."""
    text = update.message.text
    if not await is_valid_time(text):
        await update.message.reply_text(
            'Нет такое время не пойдет!'
            '\nТолько такой формат -> чч:мм!'
            '\nПопробуй ещё разок дружок пирожок:')
        return EVENT_TIME
    context.user_data['event']['time'] = text
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, 'Введи длительность в часах:')
    return EVENT_DURATION


async def get_event_duration(update: Update, context: CallbackContext):
    """
    Функция принимает и проверяет длительность события.
    В случе успеха создает событие по заданным параметрам.
    """
    duration = update.message.text
    try:
        duration = int(duration)
        if 0 < duration <= 12:
            pass
        else:
            await update.message.reply_text(
                'Ни куда не годится!'
                '\nНе больше 12 часов!'
                '\nПопробуй ещё разок дружок пирожок:')
            return EVENT_DURATION
    except ValueError:
        await update.message.reply_text(
            'Ни куда не годится!'
            '\nТолько цифра!'
            '\nПопробуй ещё разок дружок пирожок:')
        return EVENT_DURATION

    event = context.user_data["event"]
    date_str = f'{event["date"]} {event["time"]}:00.123000'
    start_datetime = datetime.strptime(date_str, '%d-%m-%Y %H:%M:%S.%f')

    end_datetime = start_datetime + timedelta(hours=duration)
    event['start_datetime'] = start_datetime.isoformat()
    event['end_datetime'] = end_datetime.isoformat()

    await post_event(
        name=event['name'],
        description=event['description'],
        telegram_id=event['chat_id'],
        place_id=event['place_id'],
        start_datetime=event['start_datetime'],
        end_datetime=event['end_datetime']
        )

    context.user_data.clear()
    await update.message.reply_text('Событие создано!')

    return ConversationHandler.END


async def search_place(update: Update, context: CallbackContext):
    """
    Функция запускает переписку с пользователем.
    Пользователь последовательно вводит имя места и регион.
    Последняя функция в цепочке выводит результат поиска по параметрам.
    """
    context.user_data['search'] = {}
    context.user_data['search']['chat_id'] = str(
        update.message.from_user.id)

    await update.message.reply_text(
        'В целях безопасности поиск ограничен в выдаче.'
        '\nВведи название заведения:')
    return SEARCH_NAME


async def search_name(update: Update, context: CallbackContext):
    """Функция принимает и проверяет имя места."""
    text = update.message.text
    match = re.match(r'^\s*[a-zA-Zа-яА-Я\s]{1,25}\s*$', text)
    if not match:
        await update.message.reply_text(
            'Нет такое имя не пойдет!'
            '\nТолько буквы. Не больше 25 символов!'
            '\nПопробуй ещё разок дружок пирожок:')
        return SEARCH_NAME

    search = context.user_data["search"]

    search['place_name'] = text

    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id, 'Введи название региона или города или района:')
    return SEARCH_REGION_NAME


async def search_region_name(update: Update, context: CallbackContext):
    """
    Функция принимает и проверяет название региона.
    В случае успеха запускает поиск с заданными параметрами.
    """
    text = update.message.text
    match = re.match(r'^\s*[a-zA-Zа-яА-Я\s]{1,25}\s*$', text)
    if not match:
        await update.message.reply_text(
            'Нет такое название не пойдет!'
            '\nТолько буквы. Не больше 25 символов!'
            '\nПопробуй ещё разок дружок пирожок:')
        return SEARCH_REGION_NAME

    search = context.user_data["search"]
    search['region_name'] = text
    search_data = {
        'chat_id': search['chat_id'],
        'region_name': search['region_name'],
        'place_name': search['place_name']
    }

    await handle_location(
        update,
        context,
        search_data=search_data,
        )

    context.user_data.clear()

    return ConversationHandler.END


def main():
    """Основная логика работы бота."""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler('start', start))

    location_handler = MessageHandler(filters.LOCATION, handle_location)
    application.add_handler(location_handler)

    user_subscription = MessageHandler(
            filters.TEXT & filters.Regex(
                r'🕺 Подписки 🕺'), user_subscriptions)
    application.add_handler(user_subscription)

    application.add_handler(CallbackQueryHandler(
        details_button, pattern="details_button"))
    application.add_handler(CallbackQueryHandler(
        create_fast_event_button, pattern="create_fast_event_button"))
    application.add_handler(CallbackQueryHandler(
        add_favorite_button, pattern="add_favorite_button"))
    application.add_handler(CallbackQueryHandler(
        confirm_parti_button, pattern="confirm_parti_button"))
    application.add_handler(CallbackQueryHandler(
        delete_favorite_button, pattern="delete_favorite_button"))
    application.add_handler(CallbackQueryHandler(
        delete_subscribe_button, pattern="delete_subscribe_button"))
    application.add_handler(CallbackQueryHandler(
        add_subscribe_button, pattern="add_subscribe_button"))

    conversation_handler = ConversationHandler(
        entry_points=[MessageHandler(
            filters.TEXT & filters.Regex(
                r'^/create_event_\d+'), create_event)],
        states={
            EVENT_NAME: [MessageHandler(
                filters.TEXT & (~filters.COMMAND), get_event_name)],
            EVENT_DESCRIPTION: [MessageHandler(
                filters.TEXT & (~filters.COMMAND), get_event_description)],
            EVENT_DATE: [MessageHandler(
                filters.TEXT & (~filters.COMMAND), get_event_date)],
            EVENT_TIME: [MessageHandler(
                filters.TEXT & (~filters.COMMAND), get_event_time)],
            EVENT_DURATION: [MessageHandler(
                filters.TEXT & (~filters.COMMAND), get_event_duration)],
        },
        fallbacks=[]
    )
    application.add_handler(conversation_handler)

    search_by_handler = ConversationHandler(
        entry_points=[MessageHandler(
            filters.TEXT & filters.Regex(
                r'^Поиск'), search_place)],
        states={
            SEARCH_NAME: [MessageHandler(
                filters.TEXT & (~filters.COMMAND), search_name)],
            SEARCH_REGION_NAME: [MessageHandler(
                filters.TEXT & (~filters.COMMAND), search_region_name)],
        },
        fallbacks=[]
    )
    application.add_handler(search_by_handler)

    echo_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(echo_handler)

    unknown_handler = MessageHandler(filters.COMMAND, handle_command)
    application.add_handler(unknown_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    logging.basicConfig(
        filename='Event_Explorer.log',
        format='%(asctime)s - %(name)s - %(levelname)s - LINE: %(lineno)d'
        ' - FUNCTION: %(funcName)s - MESSAGE: %(message)s',
        level=logging.INFO,
        filemode='w'
    )
    main()
