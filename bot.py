from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import asyncio
import os

# Отладка: покажи все переменные окружения
print("🔍 ВСЕ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
for key, value in os.environ.items():
    if "TOKEN" in key.upper():
        print(f"✅ Найдено: {key} = {value[:15]}...")

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN = None")
    print("📋 Доступные переменные:", list(os.environ.keys()))
    exit(1)

print(f"✅ Запуск бота с токеном: {TOKEN[:10]}...")

bot = Bot(token=TOKEN)
dp = Dispatcher()

kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🔘 Энергия на нуле"), KeyboardButton(text="🔘 Раздражён")],
    [KeyboardButton(text="🔘 Норм"), KeyboardButton(text="🔘 Всё ровно")]
], resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("👋 *Привет. Это Рубеж.*", parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
