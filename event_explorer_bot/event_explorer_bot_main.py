import os
from dotenv import load_dotenv
import logging

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (filters, MessageHandler, ApplicationBuilder,
                          CommandHandler, ContextTypes, CallbackContext,
                          CallbackQueryHandler)

from get_backend_response import (get_command_response,
                                  get_message_response,
                                  get_location_response)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Im a bot, please talk to me!'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    message = update.message.text
    text = await get_message_response(message, chat_id)
    response_text = f"{text}"
    await context.bot.send_message(chat_id=chat_id, text=response_text)


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

            keyboard = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(
                        'Смотреть на карте',
                        callback_data=(f'b1|{element_id}|'
                                       f'{name}|'
                                       f'{response_lat}|'
                                       f'{response_lon}')
                        )],
                ]
            )

            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML)


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
            [InlineKeyboardButton(
                "Создам событие на потом",
                callback_data=f'b3|{element_id}'
                )],
        ]
    )
    await context.bot.send_location(
        chat_id=chat_id,
        latitude=latitude,
        longitude=longitude,
        reply_markup=keyboard,)


async def b2(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.from_user.id

    callback_data_parts = update.callback_query.data.split("|")

    element_id = callback_data_parts[1]

    await context.bot.send_message(
        chat_id,
        f'Тут событие будет создаваться автоматически для id = {element_id}')


async def b3(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.from_user.id

    callback_data_parts = update.callback_query.data.split("|")

    element_id = callback_data_parts[1]

    await context.bot.send_message(
        chat_id,
        f'Тут будет модуль подробного созданиясобытия для id = {element_id}')


def main():
    """Основная логика работы бота."""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler('start', start))

    echo_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(echo_handler)

    location_handler = MessageHandler(filters.LOCATION, handle_location)
    application.add_handler(location_handler)

    unknown_handler = MessageHandler(filters.COMMAND, handle_command)
    application.add_handler(unknown_handler)

    application.add_handler(CallbackQueryHandler(b1, pattern="b1"))
    application.add_handler(CallbackQueryHandler(b2, pattern="b2"))
    application.add_handler(CallbackQueryHandler(b3, pattern="b3"))

    application.run_polling()


if __name__ == '__main__':
    logging.basicConfig(
        filename='Event_Explorer.log',
        format='%(asctime)s - %(name)s - %(levelname)s - LINE: %(lineno)d'
        ' - FUNCTION: %(funcName)s - MESSAGE: %(message)s',
        level=logging.INFO,
        filemode='w'
    )
    main()
