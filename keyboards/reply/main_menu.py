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

cancel_button_2 = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отменить')]
], resize_keyboard=True)

file_adding = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Дальше'), KeyboardButton(text='Отменить')]
], resize_keyboard=True)

text_adding = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Готово'), KeyboardButton(text='Отменить')]
], resize_keyboard=True)

remove_message = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Удалить'), KeyboardButton(text='Назад')]
], resize_keyboard=True, one_time_keyboard=True)
