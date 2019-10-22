import sys

import telebot

CURRENCIES = {'RUB': 'руб.',
              'USD': 'долл.',
              'EUR': 'евро'}

ADMIN_USER_ID = -1
TOKEN = ''


def handler(username: str, amount: float, currency: str, text: str):
    """
    Обработчик доната
    :param username: строка с именем донатера
    :param amount: сумма доната
    :param currency: строка с валютой доната (RUB, USD, EUR)
    :param text: текст доната
    :return:
    """
    bot = telebot.TeleBot(TOKEN)
    bot.send_message(ADMIN_USER_ID, f'{username} задонатил {amount} {CURRENCIES[currency]} со словами: \"{text}\"')


def main():
    if len(sys.argv) < 5:
        return

    username = sys.argv[1]
    amount = float(sys.argv[2])
    currency = sys.argv[3]
    text = sys.argv[4]

    handler(username, amount, currency, text)


main()
