from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")  # Токен берем из переменных окружения

bot = Bot(token=TOKEN)
dp = Dispatcher()

kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🔘 Энергия на нуле"), KeyboardButton(text="🔘 Раздражён")],
    [KeyboardButton(text="🔘 Норм"), KeyboardButton(text="🔘 Всё ровно")]
], resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 *Привет. Это Рубеж.*\n\n"
        "Здесь не будет мотивационных соплей.\n\n"
        "Как ты сейчас?",
        reply_markup=kb,
        parse_mode="Markdown"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())