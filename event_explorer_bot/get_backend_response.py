import httpx
import asyncio


async def get_command_response(command: str, chat_id: str):
    url = f'http://0.0.0.0:8000/commands/{command}?chat_id={chat_id}'

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code == 200:
        return response.json()['response']
    else:
        return {'error': 'Failed to get the response'}


async def get_message_response(message: str, chat_id: str):
    url = f'http://0.0.0.0:8000/messages/{message}?chat_id={chat_id}'

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code == 200:
        return response.json()['response']
    else:
        return {'error': 'Failed to get the response'}


async def get_location_response(chat_id: str, latitude: str, longitude: str):
    url = ('http://0.0.0.0:8000/location/?'
           f'chat_id={chat_id}&'
           f'latitude={latitude}&'
           f'longitude={longitude}')

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code == 200:
        response_query = response.json()['response']['elements']

        return response_query
    else:
        return {'error': 'Failed to get the response'}


async def get_user(chat_id: str):
    url = f'http://0.0.0.0:8000/users/{chat_id}'

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to get the response'}


async def post_user(
        chat_id: str,
        username: str,
        first_name: str,
        last_name: str,
        language_code: str,
        is_bot: bool):

    url = 'http://0.0.0.0:8000/users/'

    data = {
        'chat_id': chat_id,
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'language_code': language_code,
        'is_bot': is_bot
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to get the response'}


async def post_event(
        name: str,
        description: str,
        chat_id: str,
        place_id: str,
        start_datetime: str,
        end_datetime: str):

    url = 'http://0.0.0.0:8000/events/'

    data = {
        'name': name,
        'description': description,
        'chat_id': chat_id,
        'place_id': place_id,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to get the response'}


async def main():
    command = 'some_command'
    result = await get_command_response(command)
    print(result)

if __name__ == '__main__':
    asyncio.run(main())
