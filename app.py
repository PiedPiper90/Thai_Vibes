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
        return  # Просто ничего не делаем в общем чате

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
                reply_markup=markup
            )

            logger.info(f"Новый участник {user_id} ({user_name}) вступил в чат")

    except Exception as e:
        logger.error(f"Ошибка при обработке нового участника: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_"))
def verify_user(call):
    """Верифицирует пользователя после нажатия кнопки"""
    try:
        chat_id = call.message.chat.id
        user_id = int(call.data.split("_")[1])

        if call.from_user.id == user_id:
            # Снимаем все ограничения
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

            logger.info(f"Пользователь {user_id} успешно верифицирован")
        else:
            bot.answer_callback_query(call.id, "Эта кнопка не для вас!")
            logger.warning(f"Пользователь {call.from_user.id} пытался нажать чужую кнопку верификации")

    except Exception as e:
        logger.error(f"Ошибка при верификации пользователя: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка. Попробуйте еще раз.")

# Webhook для Railway
@server.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    """Обрабатывает входящие обновления от Telegram"""
    try:
        json_string = request.stream.read().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}")
        return "Error", 500

@server.route("/")
def webhook():
    """Устанавливает webhook при запуске"""
    try:
        bot.remove_webhook()
        webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook установлен: {webhook_url}")
        return "Webhook set!", 200
    except Exception as e:
        logger.error(f"Ошибка при установке webhook: {e}")
        return f"Error setting webhook: {e}", 500

@server.route("/health")
def health_check():
    """Проверка здоровья сервиса"""
    return "OK", 200

# Обработчик для неизвестных команд (чтобы не было строки ввода)
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_unknown_command(message):
    """Обработчик для всех текстовых сообщений, кроме команд"""
    # Создаем клавиатуру с кнопкой "Start"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    start_button = types.KeyboardButton("/start")
    markup.add(start_button)

    # Отправляем сообщение с кнопкой "Start"
    bot.send_message(message.chat.id, "Пожалуйста, используйте команду /start", reply_markup=markup)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Запуск сервера на порту {port}")
    server.run(host="0.0.0.0", port=port, debug=False)
