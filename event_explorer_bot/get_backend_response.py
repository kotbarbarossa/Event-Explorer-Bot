import asyncio
from typing import Any, Union

import httpx

base_url = 'http://0.0.0.0:8000'


async def get_response(*args, **kwargs) -> Union[dict, Any]:
    """Получение ответа от backend."""
    endpoint = kwargs.get('endpoint')
    data = kwargs.get('data')
    method = kwargs.get('method')
    url = base_url + endpoint

    async with httpx.AsyncClient() as client:
        if method == 'post':
            response = await client.post(url, json=data)
        elif method == 'delete':
            response = await client.delete(url)
        else:
            response = await client.get(url)

    if response.status_code == 200:
        return response.json()

    return {'error': 'Failed to get the response'}


async def get_command_response(
        command: str,
        telegram_id: str) -> Union[dict, Any]:
    """Получение ответа на команду."""
    endpoint = f'/commands/{command}/?telegram_id={telegram_id}'
    response = await get_response(endpoint=endpoint)
    return response['response']


async def get_message_response(message: str, telegram_id: str):
    """Получение ответа на сообщение."""
    endpoint = f'/messages/{message}/?telegram_id={telegram_id}'
    response = await get_response(endpoint=endpoint)
    return response['response']


async def get_location_response(
        telegram_id: str,
        latitude: float,
        longitude: float) -> Union[dict, Any]:
    """Получение локаций по координатам."""
    endpoint = ('/locations/?'
                f'telegram_id={telegram_id}&'
                f'latitude={latitude}&'
                f'longitude={longitude}')
    response = await get_response(endpoint=endpoint)
    return response['response']['elements']


async def get_search_by_name_response(
        telegram_id: str,
        region_name: str,
        place_name: str) -> Union[dict, Any]:
    """Получение локаций по имени и региону."""
    endpoint = ('/locations/search/?'
                f'telegram_id={telegram_id}&'
                f'region_name={region_name}&'
                f'place_name={place_name}')
    response = await get_response(endpoint=endpoint)
    return response['response']['elements']


async def get_user(telegram_id: str) -> Union[dict, Any]:
    """Получение пользователя по telegram_id."""
    endpoint = f'/users/{telegram_id}/'
    return await get_response(endpoint=endpoint)


async def post_user(
        telegram_id: str,
        username: str,
        first_name: str,
        last_name: str,
        language_code: str,
        is_bot: bool) -> Union[dict, Any]:
    """Создание пользователя."""
    endpoint = '/users/'
    data = {
        'telegram_id': telegram_id,
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'language_code': language_code,
        'is_bot': is_bot
    }
    return await get_response(endpoint=endpoint, data=data, method='post')


async def post_event(
        name: str,
        description: str,
        telegram_id: str,
        place_id: str,
        start_datetime: str,
        end_datetime: str) -> Union[dict, Any]:
    """Создание события."""
    endpoint = '/events/'
    data = {
        'name': name,
        'description': description,
        'telegram_id': telegram_id,
        'place_id': place_id,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime
    }
    return await get_response(endpoint=endpoint, data=data, method='post')


async def post_event_subscription(
        telegram_id:
        str, event_id: int) -> Union[dict, Any]:
    """Создание подписки на событие."""
    endpoint = '/users/events/subscription/'
    data = {
        'telegram_id': telegram_id,
        'event_id': event_id,
    }
    return await get_response(endpoint=endpoint, data=data, method='post')


async def post_place_subscription(
        telegram_id: str,
        place_id: str) -> Union[dict, Any]:
    """Создание подписки на место."""
    endpoint = '/users/places/subscription/'
    data = {
        'telegram_id': telegram_id,
        'place_id': place_id,
    }
    return await get_response(endpoint=endpoint, data=data, method='post')


async def delete_place_subscription(
        telegram_id: str,
        place_id: str) -> Union[dict, Any]:
    """Удаление подписки на место."""
    endpoint = f'/users/{telegram_id}/places/subscription/?place_id={place_id}'
    return await get_response(endpoint=endpoint, method='delete')


async def get_place_subscription(telegram_id: str) -> Union[dict, Any]:
    """Получение подписок пользователя telegram_id на места."""
    endpoint = f'/users/{telegram_id}/places/subscription/'
    response = await get_response(endpoint=endpoint)
    if response.get('error'):
        return None
    return response['response']['elements']


async def get_place_detail_response(
        telegram_id: str,
        place_id: str) -> Union[dict, Any]:
    """Получение места по place_id."""
    endpoint = f'/places/{place_id}/?telegram_id={telegram_id}'
    response = await get_response(endpoint=endpoint)
    if response.get('error'):
        return None
    return response['response']['elements'][0]


async def get_user_subscription(telegram_id: str) -> Union[dict, Any]:
    """Получение подписок на пользователей по telegram_id."""
    endpoint = f'/users/{telegram_id}/subscription/'
    response = await get_response(endpoint=endpoint)
    return response['response']


async def post_user_subscription(
        telegram_id: str,
        subscription_id: str) -> Union[dict, Any]:
    """Создание подписки на пользователя subscription_id."""
    endpoint = '/users/subscription/'
    data = {
        'telegram_id': telegram_id,
        'subscription_id': subscription_id,
    }
    return await get_response(endpoint=endpoint, data=data, method='post')


async def delete_user_subscription(
        telegram_id: str,
        subscription_id: str) -> Union[dict, Any]:
    """Удаление подписки на пользователя subscription_id."""
    endpoint = (f'/users/{telegram_id}/subscription/?'
                f'subscription_id={subscription_id}')
    return await get_response(endpoint=endpoint, method='delete')


async def main():
    command = 'some_command'
    result = await get_command_response(command)
    print(result)

if __name__ == '__main__':
    asyncio.run(main())
