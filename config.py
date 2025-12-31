import os
from dotenv import load_dotenv

# Atrof-muhit o'zgaruvchilarini yuklaymiz
load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN")
ADMIN_ID: str = os.getenv("ADMIN_ID")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! .env faylni tekshiring.")