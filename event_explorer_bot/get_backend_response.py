import httpx
import asyncio

base_url = 'http://0.0.0.0:8000'


async def get_response(*args, **kwargs):
    endpoint = kwargs.get('endpoint')
    data = kwargs.get('data')
    url = base_url + endpoint

    async with httpx.AsyncClient() as client:
        if data:
            response = await client.post(url, json=data)
        else:
            response = await client.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to get the response'}


async def get_command_response(command: str, chat_id: str):
    endpoint = f'/commands/{command}?chat_id={chat_id}'
    response = await get_response(endpoint=endpoint)
    return response['response']


async def get_message_response(message: str, chat_id: str):
    endpoint = f'/messages/{message}?chat_id={chat_id}'
    response = await get_response(endpoint=endpoint)
    return response['response']


async def get_location_response(chat_id: str, latitude: str, longitude: str):
    endpoint = ('/location/?'
                f'chat_id={chat_id}&'
                f'latitude={latitude}&'
                f'longitude={longitude}')
    response = await get_response(endpoint=endpoint)
    return response['response']['elements']


async def get_user(chat_id: str):
    endpoint = f'/users/{chat_id}'
    return await get_response(endpoint=endpoint)


async def post_user(
        chat_id: str,
        username: str,
        first_name: str,
        last_name: str,
        language_code: str,
        is_bot: bool):
    endpoint = '/users/'
    data = {
        'chat_id': chat_id,
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'language_code': language_code,
        'is_bot': is_bot
    }
    return await get_response(endpoint=endpoint, data=data)


async def post_event(
        name: str,
        description: str,
        chat_id: str,
        place_id: str,
        start_datetime: str,
        end_datetime: str):
    endpoint = '/events/'
    data = {
        'name': name,
        'description': description,
        'chat_id': chat_id,
        'place_id': place_id,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime
    }
    return await get_response(endpoint=endpoint, data=data)


async def post_event_subscription(chat_id: str, event_id: int):
    endpoint = '/events/subscription/'
    data = {
        'chat_id': chat_id,
        'event_id': event_id,
    }
    return await get_response(endpoint=endpoint, data=data)


async def main():
    command = 'some_command'
    result = await get_command_response(command)
    print(result)

if __name__ == '__main__':
    asyncio.run(main())
