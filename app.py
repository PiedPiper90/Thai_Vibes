import telebot
from telebot import types
import os
import threading
from datetime import datetime, timedelta
from flask import Flask, request
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен из переменной окружения (безопасно)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID", -1002063123602))  # ID вашего чата
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "YOUR_WEBHOOK_URL")

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)

def revoke_link_later(chat_id, invite_link, delay=30):
    """Отзывает ссылку-приглашение через указанное время"""
    def worker():
        try:
            threading.Event().wait(delay)
            bot.revoke_chat_invite_link(chat_id, invite_link)
            logger.info(f"Ссылка {invite_link} отозвана через {delay} секунд")
        except Exception as e:
            logger.error(f"Ошибка при удалении ссылки {invite_link}: {e}")

    threading.Thread(target=worker, daemon=True).start()

@bot.message_handler(commands=['start'])
def send_temporary_link(message):
    if message.chat.type != "private":
        bot.send_message(
            message.chat.id,
            "Пожалуйста, напишите мне в личные сообщения, чтобы получить ссылку на чат!"
        )
        return

    try:
        expire_time = datetime.now() + timedelta(seconds=60)
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
            f"(действует 60 секунд):\n\n{invite_link}\n\n"
            f"⚠️ Поторопитесь! Ссылка исчезнет через 60 секунд."
        )

        # Дополнительно отзываем ссылку через 30 секунд (раньше истечения)
        revoke_link_later(CHAT_ID, invite_link, delay=30)

        logger.info(f"Создана ссылка {invite_link} для пользователя {message.from_user.id}")

    except Exception as e:
        error_msg = f"Ошибка при создании ссылки: {e}"
        bot.send_message(message.chat.id, error_msg)
        logger.error(error_msg)

@bot.chat_member_handler()
def on_user_join(update):
    """Обрабатывает вступление нового участника в чат"""
    try:
        chat_id = update.chat.id
        user_id = update.new_chat_member.user.id
        status = update.new_chat_member.status
        user_name = update.new_chat_member.user.first_name or "Друг"

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
                f"🌴 Добро пожаловать, {user_name}! 🌞\n\n"
                "Ты попал в уютный чат о Таиланде и Пхукете! Здесь делимся советами, впечатлениями, "
                "отвечаем на вопросы и просто общаемся по-доброму.\n\n"
                "Чтобы получить доступ к чату, пожалуйста, нажми кнопку ниже и докажи, что ты настоящий человек 😊",
                reply
