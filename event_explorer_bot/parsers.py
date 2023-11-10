import random
from datetime import datetime

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
