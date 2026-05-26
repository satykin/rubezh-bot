import asyncio
import logging
import os
from datetime import datetime

# 👇 ВАЖНО: F импортируем из корня, а не из filters или types
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ОШИБКА: Токен не найден!")
    exit(1)

print(f"✅ Запуск бота: {TOKEN[:10]}...")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРЫ ---

main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text=" Трекинг"), KeyboardButton(text=" Инструменты")],
    [KeyboardButton(text="🎙 Голос")]
], resize_keyboard=True)

mood_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text=" Энергия на нуле", callback_data="mood_low")],
    [InlineKeyboardButton(text=" Раздражен/Злость", callback_data="mood_angry")],
    [InlineKeyboardButton(text="😐 Норм/Ровно", callback_data="mood_normal")],
    [InlineKeyboardButton(text="💪 В ресурсе", callback_data="mood_good")]
])

# --- ЛОГИКА ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 *Привет. Это Рубеж.*\n\n"
        "Здесь не будет соплей. Только работа.\n"
        "Нажми 'Трекинг', чтобы зафиксировать состояние.",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )

# 👇 ИСПОЛЬЗУЕМ F.text ВМЕСТО types.F.text
@dp.message(F.text == " Трекинг")
async def cmd_track(message: types.Message):
    await message.answer(
        "Фиксируем состояние. Что сейчас?\n"
        "(Это анонимно)",
        reply_markup=mood_kb
    )

# Обработка нажатий на кнопки настроения
@dp.callback_query(lambda c: c.data.startswith('mood_'))
async def process_mood(callback_query: types.CallbackQuery):
    mood = callback_query.data.replace('mood_', '')
    user_id = callback_query.from_user.id
    
    # Логика "записи" (пока просто пишем в логи сервера)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f" ДАННЫЕ: [{timestamp}] User {user_id} выбрал: {mood}")
    
    responses = {
        'low': "Принято. Низкая энергия. Дыши глубже.",
        'angry': "Злость — это топливо. Направь её в дело.",
        'normal': "Ровный фон. Хорошо. Держи ритм.",
        'good': "Отлично. Фиксируем победу."
    }
    
    text = responses.get(mood, "Принято.")
    
    await callback_query.message.edit_text(f"✅ *Записано: {text}*")
    await callback_query.answer()

# Заглушки
@dp.message(F.text == "🛠 Инструменты")
async def cmd_tools(message: types.Message):
    await message.answer("🚧 В разработке. Скоро будет.")

@dp.message(F.text == " Голос")
async def cmd_voice(message: types.Message):
    await message.answer(" В разработке. Скоро будет.")

# --- ЗАПУСК ---
async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
