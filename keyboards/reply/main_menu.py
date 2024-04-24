from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardMarkup

main_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Добавить аккаунт')],
    [KeyboardButton(text='Подключенные аккаунты')]
], resize_keyboard=True)

back_button = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Назад')]
], resize_keyboard=True)

cancel_button = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отмена')]
], resize_keyboard=True)
