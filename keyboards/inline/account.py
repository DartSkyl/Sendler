from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup, InlineKeyboardBuilder


check_data_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='✅ Все верно!', callback_data='correct')],
    [InlineKeyboardButton(text='Изменить имя', callback_data='change_name')],
    [InlineKeyboardButton(text='Изменить api_id', callback_data='change_api_id')],
    [InlineKeyboardButton(text='Изменить api_hash', callback_data='change_api_hash')],
    [InlineKeyboardButton(text='Изменить номер телефона', callback_data='change_phone_number')]
])


def accounts_choice(acc_list: dict) -> InlineKeyboardMarkup:
    """Создание клавиатуры со списком доступных аккаунтов"""
    accounts = InlineKeyboardBuilder()
    for acc in acc_list.keys():
        accounts.button(text=acc, callback_data=f'ac_{acc}')

    accounts.adjust(1)
    return accounts.as_markup()


menu_for_account = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Вкл/Выкл', callback_data='switch')],
    [InlineKeyboardButton(text='Обновить список чатов', callback_data='put_chats_list')],
    [InlineKeyboardButton(text='Настройки рассылки', callback_data='mailing_settings')],
    [InlineKeyboardButton(text='Сообщения для рассылки', callback_data='msg_for_mailing')]
])

action_with_messages = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить сообщение', callback_data='add_msg')],
    [InlineKeyboardButton(text='Посмотреть/Удалить сообщение', callback_data='preview_msg')]
])


mailing_sett = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Установить интервал рассылки', callback_data='interval')],
    [InlineKeyboardButton(text='Добавить сообщение', callback_data='add_mess')],
    [InlineKeyboardButton(text='Удалить сообщение', callback_data='del_mess')]
])


def messages_for_preview(mess_dict: dict) -> InlineKeyboardMarkup:
    """Создание клавиатуры для просмотра имеющихся сообщений"""
    mess_keyboard = InlineKeyboardBuilder()
    for mess in mess_dict.keys():
        mess_keyboard.button(text=mess, callback_data=f'mess_{mess}')
    mess_keyboard.adjust(1)
    return mess_keyboard.as_markup()


def messages_for_removing(mess_set: set) -> InlineKeyboardMarkup:
    """Создание клавиатуры для просмотра имеющихся сообщений"""
    mess_keyboard = InlineKeyboardBuilder()
    for mess in mess_set:
        mess_keyboard.button(text=mess, callback_data=f'rem_{mess}')
    mess_keyboard.adjust(1)
    return mess_keyboard.as_markup()

