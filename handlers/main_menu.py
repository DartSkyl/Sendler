from loader import dp

from aiogram.types import Message, FSInputFile
from aiogram import F, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest


@dp.message(Command('start'))
async def start_func(msg: Message):
    """Здесь происходит старт бота"""
    await msg.answer(text=f'Приветствую тебя, {msg.from_user.first_name}!\n'
                          f'Ну что, начнем? 😉')
