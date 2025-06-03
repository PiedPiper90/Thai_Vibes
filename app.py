import telebot
from telebot import types
import os
import threading
from datetime import datetime, timedelta

BOT_TOKEN = "7426978790:AAEaAZJIv2sZnoH1BAeSJ6zPMBXfnqZ2Prw"
CHAT_ID = -1002063123602  # ID вашего чата

bot = telebot.TeleBot(BOT_TOKEN)

def revoke_link_later(chat_id, invite_link, delay=10):
    # Функция для удаления ссылки через delay секунд
    def worker():
        try:
            threading.Event().wait(delay)
            bot.revoke_chat_invite_link(chat_id, invite_link)
        except Exception as e:
            print(f"Ошибка при удалении ссылки: {e}")
    threading.Thread(target=worker).start()

@bot.message_handler(commands=['link'])
def send_temporary_link(message):
    try:
        # Создаем ссылку, действующую 10 секунд, только для одного пользователя
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

        # Запускаем удаление ссылки через 10 секунд
        revoke_link_later(CHAT_ID, invite_link, delay=10)

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при создании ссылки: {e}")

if __name__ == "__main__":
    bot.polling()
