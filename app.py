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
def send_temporary_link(message):
    try:
        expire_time = datetime.now() + timedelta(seconds=30)
        expire_timestamp = int(expire_time.timestamp())
        invite = bot.create_chat_invite_link(
            chat_id=CHAT_ID,
            expire_date=expire_timestamp,
            member_limit=1
        )
        invite_link = invite.invite_link

        bot.send_message(
            message.chat.id,
            f"🌴 Добро пожаловать!\n\n"
            f"Ваша уникальная ссылка для входа в чат о Таиланде и Пхукете "
            f"(действует 10 секунд):\n\n{invite_link}\n\n"
            f"⚠️ Поторопитесь! Ссылка исчезнет через 10 секунд."
        )

        revoke_link_later(CHAT_ID, invite_link, delay=10)

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при создании ссылки: {e}")

@bot.chat_member_handler()
def on_user_join(update):
    chat_id = update.chat.id
    user_id = update.new_chat_member.user.id
    status = update.new_chat_member.status

    if status == "member":
        # Ограничиваем пользователя (не может писать)
        bot.restrict_chat_member(
            chat_id,
            user_id,
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )

        # Кнопка "Я человек"
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Я человек", callback_data=f"verify_{user_id}")
        markup.add(btn)

        bot.send_message(
            chat_id,
            f"🌴 Добро пожаловать, {update.new_chat_member.user.first_name}! 🌞\n\n"
            "Ты попал в уютный чат о Таиланде и Пхукете! Здесь делимся советами, впечатлениями, "
            "отвечаем на вопросы и просто общаемся по-доброму.\n\n"
            "Чтобы получить доступ к чату, пожалуйста, нажми кнопку ниже и докажи, что ты настоящий человек 😊",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_"))
def verify_user(call):
    chat_id = call.message.chat.id
    user_id = int(call.data.split("_")[1])

    if call.from_user.id == user_id:
        bot.restrict_chat_member(
            chat_id,
            user_id,
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        bot.answer_callback_query(call.id, "Доступ открыт! Добро пожаловать в наш тёплый чат 🌺")
        bot.edit_message_text(
            "Спасибо за подтверждение! Теперь ты полноценный участник нашего тайского сообщества. "
            "Не стесняйся задавать вопросы и делиться впечатлениями! 🏝️",
            chat_id,
            call.message.message_id
        )
    else:
        bot.answer_callback_query(call.id, "Эта кнопка не для вас!")

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

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
