from config_data.config import BOT_TOKEN

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage


bot = Bot(token=BOT_TOKEN, parse_mode="HTML", disable_web_page_preview=True)
dp = Dispatcher(bot=bot, storage=MemoryStorage())
