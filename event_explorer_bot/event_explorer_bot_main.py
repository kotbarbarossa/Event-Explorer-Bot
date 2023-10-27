import os
from dotenv import load_dotenv
import logging
import re
from datetime import datetime, timedelta
import random

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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
                                  post_event_subscription)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

emoji_list = ['😄', '🎉', '🥳', '🎈', '🌟', '🎁', '🎂', '🍾', '🎊', '🥂',
              '🤩', '🍰', '🎆', '🎇', '🎗️', '🎀', '🧨', '🪅', '🎵', '🎷',
              '🎸', '🎶', '🍸', '🍹', '🍻', '🕺', '💃', '🕶️', '📸', '🌈']


emoji_professions_list = ['👮', '🕵️', '👷', '👩‍🚒', '👨‍🌾', '👩‍🍳', '👨‍🎓',
                          '👩‍🏫', '👨‍🎤', '👩‍🎨', '👨‍🚀', '👩‍⚖️', '👨‍🦼', '👩‍🦯',
                          '🧕', '🧙‍♂️', '🧛‍♀️', '🧝‍♂️', '🧞‍♀️', '🧜‍♂️', '🦸‍♀️',
                          '🦹‍♂️', '🦺', '🤴', '👸', '🎅', '🧑‍🎓', '🧑‍🏫',
                          '🧑‍🎤', '🧑‍🎨', '🧑‍🚀', '🧑‍⚖️', '🧑‍🦼', '🧑‍🦯', '🦰',
                          '🦱', '🦳', '🦲', '👩‍⚕️', '👨‍⚕️', '👩‍🔬', '👨‍🔬',
                          '👩‍💼', '👨‍💼', '👩‍🌾', '👨‍🌾', '👩‍🍳', '👨‍🍳', '👩‍🎤',
                          '👨‍🎤', '👩‍🎨', '👨‍🎨', '👩‍🚀', '👨‍🚀', '👩‍⚖️', '👨‍⚖️',
                          '👩‍🦯', '👨‍🦯', '🦫', '🦭', '🐈‍⬛', '🦮', '🦙',
                          '🦥', '🦦', '🦨', '🦩']

NAME, DESCRIPTION, DATE, TIME, DURATION = range(5)

names_list = [
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = await get_user(chat_id)
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
            chat_id=user_id,
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
            text=text
            )
    else:
        text = 'Рад снова тебя видеть!'
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    message = update.message.text
    text = await get_message_response(message, chat_id)
    await context.bot.send_message(chat_id=chat_id, text=text)


async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.replace('/', '')
    chat_id = update.effective_chat.id
    text = await get_command_response(command, chat_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    latitude = update.message.location.latitude
    longitude = update.message.location.longitude

    response = await get_location_response(chat_id, latitude, longitude)
    for element in response:
        if element['tags'].get('name'):
            element_id = element['id']
            events = element.get('events')

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

            response_lat = element['lat']
            response_lon = element['lon']

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

            buttons = [
                    [InlineKeyboardButton(
                        'Смотреть на карте',
                        callback_data=(f'b1|{element_id}|'
                                       f'{name}|'
                                       f'{response_lat}|'
                                       f'{response_lon}')
                        )],
                ]

            if events:
                text += f'\n\n<b>Найдено {len(events)} событий:</b>'
                for event in events:
                    time_obj_start = datetime.fromisoformat(
                        event.get('start_datetime'))
                    time_obj_end = datetime.fromisoformat(
                        event.get('end_datetime'))

                    event_wnen = time_obj_start.strftime('%d/%m/%Y')
                    event_id = event.get('id')
                    event_name = event.get('name')
                    event_description = event.get('description')
                    # event_user_id = event.get('user_id')

                    if event.get('telegram_username'):
                        event_tg_username = (
                            f'@{event.get("telegram_username")}')
                    else:
                        event_tg_username = 'Безымянный Джо'
                    event_start = time_obj_start.strftime('%H:%M')
                    event_end = time_obj_end.strftime('%H:%M')
                    event_participants = event.get('event_participants')

                    emoji_one = random.choice(emoji_list)
                    emoji_two = random.choice(emoji_list)
                    emoji_three = random.choice(emoji_list)

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
                            text += f'\n{random.choice(emoji_list)} '
                            text += f'{tg_username}'
                    text += '\n'
                    event_button = [InlineKeyboardButton(
                        f'пойду к {event_tg_username} на {event_name}',
                        callback_data=(
                            f'b4|'
                            f'{event_id}|'
                            f'{event_name}'
                            )
                        )
                        ]
                    buttons.append(event_button)

            keyboard = InlineKeyboardMarkup(buttons)

            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                    )
            except Exception:
                cleaned_name = re.sub(r'[^a-zA-Zа-яА-Я]', '', name)

                logging.critical(
                    f'Функцией {handle_location.__name__} '
                    f'получено глючное имя "{name}" .'
                    f'Исправлено и передано в кнопку как "{cleaned_name}".')

                keyboard = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(
                            'Смотреть на карте',
                            callback_data=(f'b1|{element_id}|'
                                           f'{cleaned_name}|'
                                           f'{response_lat}|'
                                           f'{response_lon}')
                            )],
                    ]
                )
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML
                    )


async def b1(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.from_user.id
    callback_data = query.data.split('|')
    element_id = callback_data[1]
    name = callback_data[2]
    latitude = callback_data[3]
    longitude = callback_data[4]
    emoji = "⬇"
    text = f'Чтобы узнать маршрут\nдо <b>{name}</b>\nнажми на карту {emoji}.'

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.HTML)

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(
                "Пойду сейчас",
                callback_data=f'b2|{element_id}'
                )],
            # [InlineKeyboardButton(
            #     "Создам событие на потом",
            #     callback_data=f'b3|{element_id}|{name}'
            #     )],
        ]
    )
    await context.bot.send_location(
        chat_id=chat_id,
        latitude=latitude,
        longitude=longitude,
        reply_markup=keyboard,
        )
    await context.bot.send_message(
        chat_id,
        f'Чтобы создать событие с параметрами жми сюда {emoji} '
        f'\n/create_event_place_{element_id}',
        # reply_markup=keyboard,
        )


async def b2(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.from_user.id

    callback_data_parts = update.callback_query.data.split("|")

    element_id = callback_data_parts[1]

    start_datetime = datetime.now()
    end_datetime = start_datetime + timedelta(hours=3)

    random_name = random.choice(names_list)

    await post_event(
        name=random_name,
        description='',
        chat_id=str(chat_id),
        place_id=element_id,
        start_datetime=start_datetime.isoformat(),
        end_datetime=end_datetime.isoformat())

    await context.bot.send_message(
        chat_id,
        'Событие создано!')


# async def b3(update: Update, context: CallbackContext):
#     query = update.callback_query
#     chat_id = query.from_user.id

#     callback_data_parts = update.callback_query.data.split("|")

#     element_id = callback_data_parts[1]
#     element_name = callback_data_parts[2]

#     await create_event_place(update, context, element_id=element_id)
#     await context.bot.send_message(
#         chat_id, f'/create_event_location {element_id}')


async def b4(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = str(query.from_user.id)

    callback_data_parts = update.callback_query.data.split("|")

    event_id = int(callback_data_parts[1])
    event_name = callback_data_parts[2]
    await post_event_subscription(chat_id=chat_id, event_id=event_id)
    await context.bot.send_message(
        chat_id,
        f'Участие в {event_name} подтверждено')


async def create_event_place(update: Update, context: CallbackContext):
    message_text = update.message.text
    match = re.match(r'^/create_event_place_(\d+)', message_text)

    if match:
        place_id = match.group(1)
        context.user_data['event'] = {}
        context.user_data['event']['place_id'] = place_id
        context.user_data['event']['chat_id'] = str(
            update.message.from_user.id)

        await update.message.reply_text('Введи название события:')
        return NAME
    else:
        update.message.reply_text(
            'Неверный формат команды. '
            'Используйте /create_event_place_<place_id>')
        return ConversationHandler.END


async def name(update: Update, context: CallbackContext):
    text = update.message.text
    match = re.match(r'^[a-zA-Zа-яА-Я]{1,25}$', text)
    if not match:
        await update.message.reply_text(
            'Нет такое имя не пойдет!'
            '\nТолько буквы. Не больше 25 символов!'
            '\nПопробуй ещё разок дружок пирожок:')
        return NAME
    context.user_data['event']['name'] = text
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, 'Введи описание события:')
    return DESCRIPTION


async def description(update: Update, context: CallbackContext):
    text = update.message.text
    match = re.match(r'^[a-zA-Zа-яА-Я]{1,25}$', text)
    if not match:
        await update.message.reply_text(
            'Нет такое описание не пойдет!'
            '\nТолько буквы. Не больше 25 символов!'
            '\nПопробуй ещё разок дружок пирожок:')
        return DESCRIPTION
    context.user_data['event']['description'] = text
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, 'Введи дату события (дд-мм-гггг):')
    return DATE


async def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, '%d-%m-%Y')
        return True
    except ValueError:
        return False


async def date(update: Update, context: CallbackContext):
    text = update.message.text
    if not await is_valid_date(text):
        await update.message.reply_text(
            'Нет такая дата не пойдет!'
            '\nТолько такой формат -> дд-мм-гггг!'
            '\nПопробуй ещё разок дружок пирожок:')
        return DATE
    context.user_data['event']['date'] = text
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, 'Введи время начала (чч:мм):')
    return TIME


async def is_valid_time(time_str):
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False


async def time(update: Update, context: CallbackContext):
    text = update.message.text
    if not await is_valid_time(text):
        await update.message.reply_text(
            'Нет такое время не пойдет!'
            '\nТолько такой формат -> чч:мм!'
            '\nПопробуй ещё разок дружок пирожок:')
        return TIME
    context.user_data['event']['time'] = text
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id, 'Введи длительность в часах:')
    return DURATION


async def duration(update: Update, context: CallbackContext):
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
            return DURATION
    except ValueError:
        await update.message.reply_text(
            'Ни куда не годится!'
            '\nТолько цифра!'
            '\nПопробуй ещё разок дружок пирожок:')
        return DURATION

    event = context.user_data["event"]
    date_str = f'{event["date"]} {event["time"]}:00.123000'
    start_datetime = datetime.strptime(date_str, '%d-%m-%Y %H:%M:%S.%f')

    end_datetime = start_datetime + timedelta(hours=duration)
    event['start_datetime'] = start_datetime.isoformat()
    event['end_datetime'] = end_datetime.isoformat()

    await post_event(
        name=event['name'],
        description=event['description'],
        chat_id=event['chat_id'],
        place_id=event['place_id'],
        start_datetime=event['start_datetime'],
        end_datetime=event['end_datetime']
        )

    context.user_data.clear()
    await update.message.reply_text('Событие создано!')

    return ConversationHandler.END


def main():
    """Основная логика работы бота."""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler('start', start))

    location_handler = MessageHandler(filters.LOCATION, handle_location)
    application.add_handler(location_handler)

    application.add_handler(CallbackQueryHandler(b1, pattern="b1"))
    application.add_handler(CallbackQueryHandler(b2, pattern="b2"))
    # application.add_handler(CallbackQueryHandler(b3, pattern="b3"))
    application.add_handler(CallbackQueryHandler(b4, pattern="b4"))

    conversation_handler = ConversationHandler(
        entry_points=[MessageHandler(
            filters.TEXT & filters.Regex(
                r'^/create_event_place_\d+'), create_event_place)],
        states={
            NAME: [MessageHandler(
                filters.TEXT & (~filters.COMMAND), name)],
            DESCRIPTION: [MessageHandler(
                filters.TEXT & (~filters.COMMAND), description)],
            DATE: [MessageHandler(
                filters.TEXT & (~filters.COMMAND), date)],
            TIME: [MessageHandler(
                filters.TEXT & (~filters.COMMAND), time)],
            DURATION: [MessageHandler(
                filters.TEXT & (~filters.COMMAND), duration)],
        },
        fallbacks=[]
    )
    application.add_handler(conversation_handler)

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
