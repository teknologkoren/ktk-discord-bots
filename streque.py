import requests
from config import STREQUE_URL, STREQUE_TOKEN


def get_request(path):
    return requests.get(
        f'{STREQUE_URL}{path}',
        headers={'Authorization': f'Bearer {STREQUE_TOKEN}'}
        ).json()


def post_request(path):
    return requests.post(
        f'{STREQUE_URL}{path}',
        headers={'Authorization': f'Bearer {STREQUE_TOKEN}'}
        ).json()


def get_random_quote():
    return get_request('/quotes/random')


def get_quote(quote_id):
    return get_request(f'/quotes/{quote_id}')
