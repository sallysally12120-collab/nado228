import os
import random
import json
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------- Конфигурация ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан!")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ---------- База городов (для простоты — встроенная) ----------
CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань",
    "Нижний Новгород", "Челябинск", "Омск", "Самара", "Ростов-на-Дону",
    "Уфа", "Красноярск", "Воронеж", "Пермь", "Волгоград",
    "Краснодар", "Саратов", "Тюмень", "Тольятти", "Ижевск",
    "Барнаул", "Иркутск", "Ульяновск", "Хабаровск", "Владивосток",
    "Ярославль", "Махачкала", "Томск", "Оренбург", "Кемерово",
    "Новокузнецк", "Рязань", "Астрахань", "Набережные Челны", "Пенза",
    "Липецк", "Киров", "Чебоксары", "Калининград", "Тула",
    "Курск", "Ставрополь", "Сочи", "Тверь", "Магнитогорск",
    "Иваново", "Брянск", "Белгород", "Сургут", "Владимир"
]
# Для быстрого поиска по первой букве и проверки существования
CITIES_SET = set(CITIES)
# Словарь для группировки городов по последней букве (для выбора ботом)
CITIES_BY_LAST_LETTER = {}
for city in CITIES:
    last = city[-1].lower()
    CITIES_BY_LAST_LETTER.setdefault(last, []).append(city)

# ---------- Игровые состояния (в памяти) ----------
# Ключ: chat_id, значение: dict с данными игры
games = {}

def get_game(chat_id):
    if chat_id not in games:
        games[chat_id] = {
            "used": set(),          # уже названные города
            "last_letter": None,    # на какую букву надо назвать следующий город
            "score": 0,             # очки пользователя
            "is_active": False
        }
    return games[chat_id]

# ---------- Клавиатуры ----------
def main_menu_keyboard():
    """Главная инлайн-клавиатура"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_new = InlineKeyboardButton("🆕 Новая игра", callback_data="new_game")
    btn_rules = InlineKeyboardButton("📖 Правила", callback_data="rules")
    btn_stats = InlineKeyboardButton("📊 Статистика", callback_data="stats")
    btn_giveup = InlineKeyboardButton("🏳️ Сдаться", callback_data="giveup")
    keyboard.add(btn_new, btn_rules)
    keyboard.add(btn_stats, btn_giveup)
    return keyboard

def city_choice_keyboard(city_name):
    """Кнопка для подтверждения, что пользователь назвал город (для удобства)"""
    # Можно добавить кнопку "Сдаться" и "Новая игра", но оставим только основную
    keyboard = InlineKeyboardMarkup(row_width=1)
    btn_ok = InlineKeyboardButton("✅ Принять", callback_data="accept_city")
    # Используем callback_data для обработки ввода, но мы будем ловить текстовые сообщения
    return main_menu_keyboard()  # пока просто возвращаем главное меню

# ---------- Обработчики команд ----------
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    game = get_game(chat_id)
    game["is_active"] = False
    text = (
        "🏙️ *Добро пожаловать в игру «Города»!*\n\n"
        "Я называю город, а ты — следующий на *последнюю букву* моего.\n"
        "Поехали? Нажми кнопку *«Новая игра»* ниже!"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    game = get_game(chat_id)
    data = call.data

    if data == "new_game":
        start_new_game(chat_id, call.message)
        bot.answer_callback_query(call.id, "Игра начата!")

    elif data == "rules":
        rules = (
            "📖 *Правила игры:*\n\n"
            "1️⃣ Я называю город.\n"
            "2️⃣ Ты называешь город на *последнюю букву* моего города.\n"
            "3️⃣ Город не должен повторяться.\n"
            "4️⃣ Если не знаешь — нажми «Сдаться».\n"
            "5️⃣ За каждый правильный ответ ты получаешь +1 очко.\n\n"
            "Удачи! 🍀"
        )
        bot.edit_message_text(rules, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        bot.answer_callback_query(call.id)

    elif data == "stats":
        stats = (
            f"📊 *Твоя статистика:*\n\n"
            f"🎯 Очков: {game['score']}\n"
            f"🏙️ Названо городов: {len(game['used'])}\n"
            f"🔄 Игра активна: {'Да' if game['is_active'] else 'Нет'}"
        )
        bot.edit_message_text(stats, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        bot.answer_callback_query(call.id)

    elif data == "giveup":
        if not game["is_active"]:
            bot.answer_callback_query(call.id, "Игра ещё не начата!")
            return
        game["is_active"] = False
        text = (
            f"🏳️ Ты сдался!\n"
            f"Названо городов: {len(game['used'])}, очков: {game['score']}.\n"
            "Можешь начать новую игру кнопкой ниже."
        )
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        bot.answer_callback_query(call.id)

    elif data == "accept_city":
        # Этот колбэк не нужен, так как мы обрабатываем текстовые сообщения
        bot.answer_callback_query(call.id, "Просто напиши название города в чат!")

# ---------- Логика игры ----------
def start_new_game(chat_id, message=None):
    game = get_game(chat_id)
    # Выбираем случайный город, который ещё не использовали
    available = [c for c in CITIES if c not in game["used"]]
    if not available:
        # Если все города использованы — сбросим историю (или просто перезапустим)
        game["used"] = set()
        available = CITIES.copy()
    first_city = random.choice(available)
    game["used"].add(first_city)
    game["last_letter"] = first_city[-1].lower()
    game["is_active"] = True
    # Увеличиваем счёт только если это не первый ход? Нет, первый город даёт бот, счёт не меняется.
    text = (
        f"🗺️ Я начинаю: *{first_city}*\n\n"
        f"Теперь твой ход! Назови город на букву *«{first_city[-1].upper()}»*.\n"
        "Просто напиши его в чат.\n\n"
        "Если хочешь сдаться — нажми кнопку."
    )
    if message:
        bot.edit_message_text(text, chat_id, message.message_id, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    else:
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

# Обработчик текстовых сообщений (ввод города)
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_city_input(message):
    chat_id = message.chat.id
    game = get_game(chat_id)
    if not game["is_active"]:
        bot.reply_to(message, "⚠️ Игра не активна. Нажми «Новая игра», чтобы начать.")
        return

    user_city = message.text.strip()
    # Проверяем, есть ли город в базе
    if user_city not in CITIES_SET:
        bot.reply_to(message, f"❌ Город «{user_city}» не найден в моей базе. Попробуй другой.")
        return

    # Проверяем, не использовали ли уже
    if user_city in game["used"]:
        bot.reply_to(message, f"⚠️ Город «{user_city}» уже называли. Назови другой.")
        return

    # Проверяем первую букву
    first_letter = user_city[0].lower()
    if first_letter != game["last_letter"]:
        bot.reply_to(message, f"❌ Город должен начинаться на букву *«{game['last_letter'].upper()}»*! Ты написал на «{user_city[0].upper()}».",
                     parse_mode="Markdown")
        return

    # Всё правильно — принимаем город
    game["used"].add(user_city)
    game["score"] += 1

    # Теперь бот должен ответить своим городом на последнюю букву user_city
    last_letter = user_city[-1].lower()
    # Ищем город, который начинается на эту букву и ещё не использован
    possible = [c for c in CITIES_BY_LAST_LETTER.get(last_letter, []) if c not in game["used"]]
    if not possible:
        # Бот не может ответить — пользователь победил!
        game["is_active"] = False
        win_text = (
            f"🎉 *Поздравляю! Ты выиграл!*\n"
            f"Ты назвал {len(game['used'])} городов, набрал {game['score']} очков.\n"
            f"Я не смог подобрать город на букву «{last_letter.upper()}».\n\n"
            "Можешь начать новую игру."
        )
        bot.reply_to(message, win_text, parse_mode="Markdown", reply_markup=main_menu_keyboard())
        return

    bot_city = random.choice(possible)
    game["used"].add(bot_city)
    game["last_letter"] = bot_city[-1].lower()

    response_text = (
        f"✅ Твой город *{user_city}* принят!\n"
        f"Мой ответ: *{bot_city}*\n\n"
        f"Теперь твой ход! Назови город на букву *«{bot_city[-1].upper()}»*."
    )
    bot.reply_to(message, response_text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

# ---------- Flask-эндпоинт для webhook ----------
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Unsupported media type', 415

@app.route('/')
def index():
    return "City Bot is running!"

# ---------- Запуск (для локального теста можно использовать polling) ----------
if __name__ == '__main__':
    # Для локальной разработки используй bot.polling()
    # Но для Render используем Flask
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))