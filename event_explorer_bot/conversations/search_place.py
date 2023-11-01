import re

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import (filters, MessageHandler, CallbackContext,
                          ConversationHandler,)

from get_backend_response import get_search_by_name_response

from parsers import parse_element, parse_event

SEARCH_NAME, SEARCH_REGION_NAME = range(2)


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

    chat_id = update.effective_chat.id
    response = await get_search_by_name_response(*search_data.values())

    if not response:
        return await context.bot.send_message(
            chat_id,
            'Поиск не выдал результатов 🤷‍♂️')
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
                                       )
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

    context.user_data.clear()

    return ConversationHandler.END


search_by_name_conversation = ConversationHandler(
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
