import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# 1. Получаем токен
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ОШИБКА: Токен не найден!")
    exit(1)

print(f"✅ Найден: BOT_TOKEN = {TOKEN[:15]}...")
print(f"✅ Запуск бота с токеном: {TOKEN[:10]}...")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- КЛАВИАТУРЫ ---

# Главное меню (Reply - кнопки под полем ввода)
main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📊 Трекинг"), KeyboardButton(text="🛠 Инструменты")],
    [KeyboardButton(text="🎙 Голос")]
], resize_keyboard=True)

# Меню для трекинга (Inline - кнопки внутри сообщения)
mood_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔋 Энергия на нуле", callback_data="mood_low")],
    [InlineKeyboardButton(text="😡 Раздражен/Злость", callback_data="mood_angry")],
    [InlineKeyboardButton(text="😐 Норм/Ровно", callback_data="mood_normal")],
    [InlineKeyboardButton(text="💪 В ресурсе", callback_data="mood_good")]
])

# --- ХЕНДЛЕРЫ (Логика) ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 *Привет. Это Рубеж.*\n\n"
        "Здесь не будет соплей. Только работа.\n"
        "Нажми 'Трекинг', чтобы зафиксировать состояние.",
        reply_markup=main_kb,
        parse_mode="Markdown"
    )

@dp.message(F.text == "📊 Трекинг")
async def cmd_track(message: types.Message):
    await message.answer(
        "Фиксируем состояние. Что сейчас?\n"
        "(Это анонимно, данные никуда не утекут)",
        reply_markup=mood_kb
    )

# Обработка нажатий на кнопки настроения
@dp.callback_query(lambda c: c.data.startswith('mood_'))
async def process_mood(callback_query: types.CallbackQuery):
    mood = callback_query.data.replace('mood_', '')
    
    # Здесь потом будет запись в базу данных
    # Пока просто отвечаем
    responses = {
        'low': "Принято. Низкая энергия. Рекомендую инструмент 'Дыхание' из меню.",
        'angry': "Злость — это топливо. Не дави её, направь. Идем в раздел 'Слив'.",
        'normal': "Ровный фон. Хорошо. Держи этот ритм.",
        'good': "Отлично. Фиксируем победу. Работаем."
    }
    
    text = responses.get(mood, "Принято.")
    
    await callback_query.message.edit_text(f"✅ *Записано: {text}*")
    await callback_query.answer() # Убираем часики загрузки

# Заглушки для других кнопок
@dp.message(F.text == "🛠 Инструменты")
async def cmd_tools(message: types.Message):
    await message.answer("🚧 В разработке. Скоро будет.")

@dp.message(F.text == "🎙 Голос")
async def cmd_voice(message: types.Message):
    await message.answer("🚧 В разработке. Скоро будет.")

# --- ЗАПУСК ---
async def main():
    logging.basicConfig(level=logging.INFO)
    print("✅ Бот Rubezh запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
