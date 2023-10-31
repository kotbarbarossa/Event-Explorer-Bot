import re
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import (filters, MessageHandler, CallbackContext,
                          ConversationHandler,)

from get_backend_response import post_event

[EVENT_NAME,
 EVENT_DESCRIPTION,
 EVENT_DATE,
 EVENT_TIME,
 EVENT_DURATION
 ] = range(5)


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


create_event_conversation = ConversationHandler(
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
