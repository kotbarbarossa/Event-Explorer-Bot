import os
from dotenv import load_dotenv
import logging

from telegram import (Update, InlineKeyboardMarkup, InlineKeyboardButton,
                      ReplyKeyboardMarkup)
from telegram.constants import ParseMode
from telegram.ext import (filters, MessageHandler, ApplicationBuilder,
                          CommandHandler, ContextTypes)

from get_backend_response import (get_command_response,
                                  get_message_response,
                                  get_location_response,
                                  get_user,
                                  post_user,
                                  get_place_subscription,
                                  get_search_by_name_response,
                                  get_user_subscription)

from buttons import buttons_handlers

from parsers import parse_element, parse_event

from conversations.create_event import create_event_conversation
from conversations.search_place import search_by_name_conversation

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

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
        telegram_username = (
            user['telegram_username']
            if user['telegram_username']
            else '-скрыто-@')
        button = [InlineKeyboardButton(
            "Удалить из избранного",
            callback_data=('delete_subscribe_button|'
                           f'{user_telegram_id}|'
                           f'{telegram_username}')
            )]
        keyboard = InlineKeyboardMarkup([button])
        text = f'@{telegram_username}'
        await context.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    )


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

    for handler in buttons_handlers:
        application.add_handler(handler)

    application.add_handler(create_event_conversation)

    application.add_handler(search_by_name_conversation)

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
