from aiogram.fsm.state import StatesGroup, State


class AddingAccount(StatesGroup):
    """Набор стэйтов для добавления новых аккаунтов"""
    name_input = State()
    api_id_input = State()
    api_hash_input = State()
    phone_number_input = State()
    check_data = State()
    change_name = State()
    change_api_id = State()
    change_api_hash = State()
    change_phone_number = State()
    code_input = State()


class AccountSettings(StatesGroup):
    """Стэйты для настройки аккаунтов"""
    view_account = State()
    put_chats = State()
    chats_for_mailing = State()
    msg_title = State()
    msg_files = State()
    msg_text = State()
    msg_preview = State()
    false_state = State()
    preview_mess = State()

