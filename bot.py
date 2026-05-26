import asyncio
import logging
import os
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ОШИБКА: Токен не найден!")
    exit(1)

print(f"✅ Токен принят: {TOKEN[:10]}...")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- БАЗА ДАННЫХ ---
def init_db():
    """Создаёт таблицу если её нет"""
    conn = sqlite3.connect('rubezh.db')
    cursor = conn.cursor()
    cursor.execute('''
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
    """Сохраняет настроение в БД"""
    conn = sqlite3.connect('rubezh.db')
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        'INSERT INTO tracking (user_id, mood, timestamp) VALUES (?, ?, ?)',
        (user_id, mood, timestamp)
    )
    conn.commit()
    conn.close()
    print(f"📊 СОХРАНЕНО: User {user_id} → {mood} в {timestamp}")

def get_user_stats(user_id):
    """Получает статистику пользователя"""
    conn = sqlite3.connect('rubezh.db')
    cursor = conn.cursor()
    cursor.execute('SELECT mood, COUNT(*) FROM tracking WHERE user_id = ? GROUP BY mood', (user_id,))
    stats = cursor.fetchall()
    conn.close()
    return stats

# Инициализируем БД при старте
init_db()

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
        "Нажми '📊 Трекинг', чтобы зафиксировать состояние.",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )

@dp.message(F.text == "📊 Трекинг")
async def cmd_track(message: types.Message):
    await message.answer(
        "Фиксируем состояние. Что сейчас?",
        reply_markup=mood_kb
    )

@dp.callback_query(lambda c: c.data.startswith('mood_'))
async def process_mood(callback_query: types.CallbackQuery):
    mood = callback_query.data.replace('mood_', '')
    user_id = callback_query.from_user.id
    
    # Сохраняем в БД
    save_mood(user_id, mood)
    
    responses = {
        'low': "Принято. Низкая энергия. Дыши глубже.",
        'angry': "Злость — это топливо. Направь её в дело.",
        'normal': "Ровный фон. Хорошо. Держи ритм.",
        'good': "Отлично. Фиксируем победу."
    }
    
    text = responses.get(mood, "Принято.")
    await callback_query.message.edit_text(f"✅ *Записано: {text}*")
    await callback_query.answer()

@dp.message(F.text == "📈 Статистика")
async def cmd_stats(message: types.Message):
    user_id = message.from_user.id
    stats = get_user_stats(user_id)
    
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
    for mood, count in stats:
        name = mood_names.get(mood, mood)
        text += f"{name}: {count} раз(а)\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🛠 Инструменты")
async def cmd_tools(message: types.Message):
    await message.answer("🚧 В разработке. Скоро будет.")

# --- ЗАПУСК ---
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Бот Rubezh запущен с базой данных...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
