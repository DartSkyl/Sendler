from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup


check_data_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Все верно!', callback_data='correct')],
    [InlineKeyboardButton(text='Изменить имя', callback_data='change_name')],
    [InlineKeyboardButton(text='Изменить api_id', callback_data='change_api_id')],
    [InlineKeyboardButton(text='Изменить api_hash', callback_data='change_api_hash')],
    [InlineKeyboardButton(text='Изменить номер телефона', callback_data='change_phone_number')]
])
