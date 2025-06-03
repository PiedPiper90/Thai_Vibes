import telebot
from telebot import types
import os
from flask import Flask, request

BOT_TOKEN = "7426978790:AAEaAZJIv2sZnoH1BAeSJ6zPMBXfnqZ2Prw"
PRIVATE_CHAT_LINK = "https://t.me/+_oVu5U6o31A2OGQy"

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("получить ссылку на чат", callback_data="get_link")
    markup.add(button)
    bot.send_message(
        message.chat.id,
        "Добро пожаловать! Нажмите кнопку ниже, чтобы получить ссылку на чат:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "get_link")
def send_chat_link(call):
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        f"Вот ссылка на мой приватный чат:\n{PRIVATE_CHAT_LINK}"
    )

@server.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    # Замените на ваш Railway URL после деплоя
    webhook_url = os.environ.get("RAILWAY_STATIC_URL", "https://your-app.up.railway.app")
    bot.set_webhook(url=webhook_url + '/' + BOT_TOKEN)
    return "Webhook set!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))