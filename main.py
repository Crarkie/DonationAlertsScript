import json
import subprocess
from json import JSONDecodeError
from threading import Thread
from time import sleep
from typing import Dict, Union

import requests
from flask import Flask, request
from werkzeug.utils import redirect

config = {}
app = Flask(__name__)
SERVER_URL = 'http://localhost'
CLIENT_ID = -1
CLIENT_SECRET = ''

OAUTH_URL = f'https://www.donationalerts.com/oauth/authorize?client_id={CLIENT_ID}' \
            f'&scope=oauth-donation-index&response_type=code&redirect_uri={SERVER_URL}/authorize'
OAUTH_TOKEN_URL = f'https://www.donationalerts.com/oauth/token'


def update_config(conf: Dict[str, Union[str, int]]):
    global config
    config = conf

    with open('config.json', 'w') as config_file:
        config_file.write(json.dumps(conf, indent=4))


@app.route('/')
def index():
    return redirect(OAUTH_URL)


@app.route('/authorize')
def authorize():
    global config
    if 'code' in request.args:
        code = request.args.get('code')

        params = {
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'redirect_uri': f'{SERVER_URL}/authorize'
        }

        response = requests.post(OAUTH_TOKEN_URL, data=params).json()
        update_config(response)
        return redirect('https://donationalerts.ru')


def load_config():
    global config
    try:
        with open('config.json', 'r') as config_file:
            config = json.loads(config_file.read())
    except (FileNotFoundError, JSONDecodeError):
        return


def refresh_token():
    global config

    params = {
        'grant_type': 'refresh_token',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': config['refresh_token'],
        'redirect_uri': f'{SERVER_URL}/authorize',
        'scope': 'oauth-donation-index'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.post(OAUTH_TOKEN_URL, data=params, headers=headers).json()
    update_config(response)


def request_api(method, *args):
    # timestamp = datetime.datetime.now().timestamp()
    # if timestamp >= config['expires_in']:
    #    refresh_token()

    headers = {
        'Authorization': f'Bearer {config["access_token"]}'
    }
    response = requests.get(f'https://www.donationalerts.com/api/v1/{method}', params=args, headers=headers)
    return response.json()


class DonationPollThread(Thread):
    def __init__(self):
        self._running = True
        try:
            with open('.last_donate', 'r') as file:
                self._last_donate_id = int(file.read())
        except (FileNotFoundError, IOError, ValueError):
            self._last_donate_id = -1
        super().__init__()

    def stop(self):
        self._running = False
        with open('.last_donate', 'w') as file:
            file.write(str(self._last_donate_id))

    def run(self):
        while self._running:
            donations = request_api('alerts/donations')['data']

            new_last_id = self._last_donate_id
            for donate in donations:
                if donate['id'] > self._last_donate_id:
                    subprocess.Popen(['python3', 'script.py',
                                      donate['username'],
                                      str(donate['amount']),
                                      donate['currency'],
                                      donate['message']])

                    if donate['id'] > new_last_id:
                        new_last_id = donate['id']
            self._last_donate_id = new_last_id
            sleep(3)


def main():
    load_config()

    poll_thread = DonationPollThread()
    poll_thread.start()
    app.run('0.0.0.0', port=8080, debug=False)

    poll_thread.stop()


if __name__ == '__main__':
    main()
