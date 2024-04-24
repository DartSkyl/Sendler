from config_data.config import BOT_TOKEN

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage


bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot=bot, storage=MemoryStorage())
