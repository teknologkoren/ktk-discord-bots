import aiohttp
from instance.config import STREQUE_URL, STREQUE_TOKEN


# Make a GET request, check that it was successful, and return the response content
# as JSON.
async def get_request(path):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f'{STREQUE_URL}{path}',
            headers={'Authorization': f'Bearer {STREQUE_TOKEN}'}
        ) as response:
            response.raise_for_status()
            return await response.json()


# Make a POST request, check that it was successful, and ignore any response content.
async def post_request(path):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f'{STREQUE_URL}{path}',
            headers={'Authorization': f'Bearer {STREQUE_TOKEN}'}
        ) as response:
            response.raise_for_status()
            return


async def get_user_by_discord(discord_user_id):
    return await get_request(f'/users/by-discord/{discord_user_id}')


async def get_random_quote():
    return await get_request('/quotes/random')


async def get_quote_by_id(quote_id):
    return await get_request(f'/quotes/{quote_id}')


async def get_latest_quote():
    return (await get_request(f'/quotes?order=desc&limit=1'))[0]


async def get_all_quotes():
    return await get_request(f'/quotes')


async def get_birthday_users(month, day):
    return await get_request(f'/users/by-birthday/{month}/{day}')


async def mark_notification_sent(notification_id):
    await post_request(
        f'/notifications/{notification_id}/mark_sent')


async def mark_notification_acknowledged(notification_id):
    await post_request(
        f'/notifications/{notification_id}/mark_acknowledged')
