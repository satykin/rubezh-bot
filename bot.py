import asyncio
import logging
import os
import sqlite3
import sys
import signal
from datetime import datetime

from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ===================== КОНФИГУРАЦИЯ =====================
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")   # ← Основная переменная
PORT = int(os.getenv("PORT", 8080))

if not TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден!")
    sys.exit(1)

if not WEBHOOK_HOST:
    print("❌ ОШИБКА: WEBHOOK_HOST не найден!")
    sys.exit(1)

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

print(f"✅ Запуск Rubezh (Webhook)")
print(f"🌍 Порт: {PORT}")
print(f"🔗 Webhook URL: {WEBHOOK_URL}")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===================== БАЗА ДАННЫХ =====================
def init_db():
    conn = sqlite3.connect('rubezh.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

def save_mood(user_id, mood):
    conn = sqlite3.connect('rubezh.db')
    timestamp = datetime.now().isoformat()
    conn.execute(
        'INSERT INTO tracking (user_id, mood, timestamp) VALUES (?, ?, ?)',
        (user_id, mood, timestamp)
    )
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    conn = sqlite3.connect('rubezh.db')
    cursor = conn.execute(
        'SELECT mood, COUNT(*) as count FROM tracking WHERE user_id = ? GROUP BY mood',
        (user_id,)
    )
    return cursor.fetchall()

init_db()

# ===================== КЛАВИАТУРЫ =====================
main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📊 Трекинг"), KeyboardButton(text="📈 Статистика")],
    [KeyboardButton(text="🛠 Инструменты")]
], resize_keyboard=True)

mood_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔋 Энергия на нуле", callback_data="mood_low")],
    [InlineKeyboardButton(text="😡 Раздражен/Злость", callback_data="mood_angry")],
    [InlineKeyboardButton(text="😐 Норм/Ровно", callback_data="mood_normal")],
    [InlineKeyboardButton(text="💪 В ресурсе", callback_data="mood_good")]
])

# ===================== ХЕНДЛЕРЫ =====================
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 *Привет. Это Рубеж.*\n\nЗдесь не будет соплей. Только работа.",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )

@dp.message(F.text == "📊 Трекинг")
async def cmd_track(message: types.Message):
    await message.answer("Фиксируем состояние. Что сейчас?", reply_markup=mood_kb)

@dp.callback_query(F.data.startswith("mood_"))
async def process_mood(callback: types.CallbackQuery):
    mood = callback.data.replace("mood_", "")
    user_id = callback.from_user.id
    save_mood(user_id, mood)

    responses = {
        'low': "Низкая энергия. Дыши глубже.",
        'angry': "Злость — это топливо. Направь её в дело.",
        'normal': "Ровный фон. Держи ритм.",
        'good': "Отлично. Фиксируем ресурс."
    }
    text = responses.get(mood, "Принято.")
    
    await callback.message.edit_text("✅ Состояние зафиксировано")
    await bot.send_message(user_id, f"*{text}*", parse_mode="Markdown")
    await callback.answer()

@dp.message(F.text == "📈 Статистика")
async def cmd_stats(message: types.Message):
    stats = get_user_stats(message.from_user.id)
    if not stats:
        await message.answer("📊 Пока нет данных.")
        return
    
    mood_names = {'low': '🔋 Низкая энергия', 'angry': '😡 Раздражение', 
                  'normal': '😐 Норм', 'good': '💪 В ресурсе'}
    
    text = "*Твоя статистика:*\n\n"
    for mood, count in stats:
        name = mood_names.get(mood, mood)
        text += f"{name}: {count} раз(а)\n"
    await message.answer(text, parse_mode="Markdown")

# ===================== WEBHOOK =====================
async def on_startup(bot: Bot):
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook установлен: {WEBHOOK_URL}")

# ===================== ЗАПУСК =====================
async def main():
    logging.basicConfig(level=logging.INFO)

    dp.startup.register(lambda: on_startup(bot))

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()
    
    print(f"🚀 Бот запущен на {WEBHOOK_URL}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
