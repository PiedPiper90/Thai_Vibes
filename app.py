import telebot
from telebot import types
import os
import threading
from datetime import datetime, timedelta
from flask import Flask, request

BOT_TOKEN = "7426978790:AAEaAZJIv2sZnoH1BAeSJ6zPMBXfnqZ2Prw"
CHAT_ID = -1002063123602  # ID вашего чата

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)

def revoke_link_later(chat_id, invite_link, delay=10):
    def worker():
        try:
            threading.Event().wait(delay)
            bot.revoke_chat_invite_link(chat_id, invite_link)
        except Exception as e:
            print(f"Ошибка при удалении ссылки: {e}")
    threading.Thread(target=worker).start()

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(
        message.chat.id,
        "Привет! Этот бот выдаёт временные ссылки для входа в чат.\n"
        "Чтобы получить ссылку, отправьте команду /link"
    )

@bot.message_handler(commands=['link'])
def send_temporary_link(message):
    try:
        expire_time = datetime.now() + timedelta(seconds=10)
        expire_timestamp = int(expire_time.timestamp())
        invite = bot.create_chat_invite_link(
            chat_id=CHAT_ID,
            expire_date=expire_timestamp,
            member_limit=1
        )
        invite_link = invite.invite_link

        bot.send_message(
            message.chat.id,
            f"Ваша уникальная ссылка для входа в чат (действует 10 секунд):\n{invite_link}"
        )

        revoke_link_later(CHAT_ID, invite_link, delay=10)

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при создании ссылки: {e}")

# Webhook для Railway
@server.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    webhook_url = "https://thaivibes-production.up.railway.app"
    bot.set_webhook(url=webhook_url + '/' + BOT_TOKEN)
    return "Webhook set!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
