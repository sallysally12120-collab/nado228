import os
import threading
import sys
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# НОВЫЙ ТОКЕН (вставлен)
TOKEN = "8311159073:AAEp3G6m4yUgSrcZCRlWy2q6V-B77lRP87g"

app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

@app.route('/health')
def health():
    return "OK"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я работаю круглосуточно в облаке!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Напиши мне что-нибудь, и я отвечу.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Вы сказали: {update.message.text}")

def run_bot():
    try:
        print("🔄 Запускаю бота...")
        bot_app = Application.builder().token(TOKEN).build()
        bot_app.add_handler(CommandHandler("start", start))
        bot_app.add_handler(CommandHandler("help", help_command))
        bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        print("🤖 Бот запущен и слушает сообщения...")
        bot_app.run_polling()
    except Exception as e:
        print(f"❌ Ошибка в боте: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)