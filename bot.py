import asyncio
import logging
import os
import sqlite3
import threading
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- КОНФИГУРАЦИЯ ---
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Токен не найден!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- БАЗА ДАННЫХ (Синхронная, но вызывается безопасно) ---
DB_NAME = "rubezh.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                mood TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        conn.commit()
    print("✅ База данных инициализирована")

def save_mood_db(user_id, mood):
    """Сохраняет настроение (выполняется в отдельном потоке)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_connection() as conn:
        conn.execute(
            'INSERT INTO tracking (user_id, mood, timestamp) VALUES (?, ?, ?)',
            (user_id, mood, timestamp)
        )
        conn.commit()
    return f"Записано: {mood} в {timestamp}"

def get_stats_db(user_id):
    """Получает статистику"""
    with get_connection() as conn:
        cursor = conn.execute(
            'SELECT mood, COUNT(*) as count FROM tracking WHERE user_id = ? GROUP BY mood',
            (user_id,)
        )
        return cursor.fetchall()

# --- КЛАВИАТУРЫ ---
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

# --- ЛОГИКА ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 *Привет. Это Рубеж.*\n\n"
        "Здесь не будет соплей. Только работа.\n"
        "Нажми ' Трекинг', чтобы зафиксировать состояние.",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )

@dp.message(F.text == "📊 Трекинг")
async def cmd_track(message: types.Message):
    await message.answer(
        "Фиксируем состояние. Что сейчас?\n*(кнопки исчезнут, ответ придет ниже)*",
        reply_markup=mood_kb
    )

@dp.callback_query(lambda c: c.data.startswith('mood_'))
async def process_mood(callback_query: types.CallbackQuery):
    mood = callback_query.data.replace('mood_', '')
    user_id = callback_query.from_user.id
    
    # 1. Сохраняем в БД в отдельном потоке (чтобы не блокировать бота)
    log_msg = await asyncio.to_thread(save_mood_db, user_id, mood)
    print(f"📊 {log_msg}")

    # 2. Отвечаем пользователю НОВЫМ сообщением (не удаляя кнопки)
    responses = {
        'low': "Принято. Низкая энергия. Дыши глубже.",
        'angry': "Злость — это топливо. Направь её в дело.",
        'normal': "Ровный фон. Хорошо. Держи ритм.",
        'good': "Отлично. Фиксируем победу."
    }
    
    text = responses.get(mood, "Принято.")
    await callback_query.answer() # Убираем "часики" загрузки
    await bot.send_message(user_id, f"✅ *{text}*", parse_mode="Markdown")

@dp.message(F.text == "📈 Статистика")
async def cmd_stats(message: types.Message):
    user_id = message.from_user.id
    stats = await asyncio.to_thread(get_stats_db, user_id)
    
    if not stats:
        await message.answer("📊 Пока нет данных. Начни трекинг!")
        return
    
    mood_names = {
        'low': '🔋 Низкая энергия',
        'angry': '😡 Раздражение',
        'normal': '😐 Норм',
        'good': '💪 В ресурсе'
    }
    
    text = "*Твоя статистика:*\n\n"
    for row in stats:
        name = mood_names.get(row['mood'], row['mood'])
        text += f"{name}: {row['count']} раз(а)\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🛠 Инструменты")
async def cmd_tools(message: types.Message):
    await message.answer("🚧 В разработке. Скоро будет.")

# --- ЗАПУСК ---
async def main():
    logging.basicConfig(level=logging.INFO)
    # Инициализация БД при старте
    await asyncio.to_thread(init_db)
    print(" Бот Rubezh запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
