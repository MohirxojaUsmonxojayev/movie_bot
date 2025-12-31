import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import router

# Loglarni sozlash (Debugging uchun juda muhim)
logging.basicConfig(level=logging.INFO, stream=sys.stdout)


async def main():
    # Bot va Dispatcher yaratamiz
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Routerni ulaymiz
    dp.include_router(router)

    print("🤖 Bot ishga tushdi...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")