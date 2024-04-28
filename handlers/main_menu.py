from loader import dp
from keyboards import main_menu, cancel_button, check_data_keyboard, accounts_choice, ask_deletion
from states import AddingAccount
from utils.account_model import Account, account_dict

from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram import F, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from pyrogram.errors.exceptions.bad_request_400 import ApiIdInvalid
from pyrogram.errors.exceptions.not_acceptable_406 import PhoneNumberInvalid


async def send_status_info(msg: Message):
    """Данная функция отправляет в чат сообщение с информацией
    о текущем статусе - сколько всего ботов подключено и сколько из них запущено"""
    count_account = len(account_dict)
    count_active_account = 0
    for account in account_dict.values():
        if account.get_active():
            count_active_account += 1
    await msg.answer(text=f'Всего подключено аккаунтов: <b>{count_account}</b>\n'
                          f'Аккаунтов активно: <b>{count_active_account}</b>', reply_markup=main_menu)


@dp.message(Command('start'))
async def start_func(msg: Message):
    """Здесь происходит старт бота"""
    await msg.answer(text=f'Приветствую тебя, {msg.from_user.first_name}!\n'
                          f'Ну что, начнем? 😉')
    await send_status_info(msg=msg)


@dp.message(F.text == '➕ Добавить аккаунт')
async def start_adding_account(msg: Message, state: FSMContext):
    """Здесь пользователь начинает добавлять новый аккаунт и задается соответствующий стэйт"""
    await state.set_state(AddingAccount.name_input)
    await msg.answer(text='Введите название для нового аккаунт:', reply_markup=cancel_button)


@dp.message(AddingAccount.name_input, F.text != '🚫 Отмена')
async def api_id_input(msg: Message, state: FSMContext):
    """Здесь мы ловим название аккаунта и предлагаем ввести api_id"""
    if '<' not in msg.text:
        await state.set_data({'name': msg.text})
        await state.set_state(AddingAccount.api_id_input)
        await msg.answer(text='Теперь введите <b>api_id</b>:')
    else:
        await msg.answer(text=html.quote('Имя не должно содержать символ "<", попробуйте еще раз!'))


@dp.message(AddingAccount.api_id_input, F.text.isdigit())
async def api_hash_input(msg: Message, state: FSMContext):
    """Здесь мы ловим api_id и предлагаем ввести api_hash"""
    await state.update_data({'api_id': msg.text})
    await state.set_state(AddingAccount.api_hash_input)
    await msg.answer(text='Теперь введите <b>api_hash</b>:')


@dp.message(AddingAccount.api_hash_input, F.text != 'Отмена')
async def phone_number_input(msg: Message, state: FSMContext):
    """Здесь мы ловим api_has и предлагаем ввести номер телефона"""
    await state.update_data({'api_hash': msg.text})
    await state.set_state(AddingAccount.phone_number_input)

    await msg.answer(text='Теперь введите номер телефона в международном формате:')


@dp.message(AddingAccount.phone_number_input, F.text.regexp(r'\+\d{10,}'))
async def phone_number_adding(msg: Message, state: FSMContext):
    """Вынесем ловлю телефона в отдельный хэндлер для удобства"""
    await state.update_data({'phone_number': msg.text})
    await state.set_state(AddingAccount.check_data)
    await check_the_data(msg=msg, state=state)


async def check_the_data(msg: Message, state: FSMContext):
    """Даем пользователю проверить правильность введенных данных и возможность их исправить"""

    account_data = await state.get_data()
    msg_text = (f'Проверьте правильность введенных данных:\n\n'
                f'<b>Имя аккаунта</b>: <i>{account_data["name"]}</i>\n'
                f'<b>api_id</b>: <i>{account_data["api_id"]}</i>\n'
                f'<b>api_hash</b>: <i>{account_data["api_hash"]}</i>\n'
                f'<b>Номер телефона</b>: <i>{account_data["phone_number"]}</i>')
    await msg.answer(text=msg_text, reply_markup=check_data_keyboard)


@dp.callback_query(AddingAccount.check_data, F.data != 'correct')
async def change_the_data(callback: CallbackQuery, state: FSMContext):
    """Здесь пользователь либо меняет какие-нибудь данные либо идет дальше"""
    await callback.answer()
    change_states = {
        'change_name': (AddingAccount.change_name, 'Введите имя:'),
        'change_api_id': (AddingAccount.change_api_id, 'Введите api_id:'),
        'change_api_hash': (AddingAccount.change_api_hash, 'Введите api_hash:'),
        'change_phone_number': (AddingAccount.change_phone_number, 'Введите номер телефона')
    }
    await state.set_state(change_states[callback.data][0])
    await callback.message.answer(text=change_states[callback.data][1])


@dp.callback_query(AddingAccount.check_data, F.data == 'correct')
async def auth_function(callback: CallbackQuery, state: FSMContext):
    """Здесь начинается авторизация добавляемого аккаунта"""
    await callback.answer()
    account_data = await state.get_data()
    new_account = Account(
        name=account_data['name'],
        api_id=account_data['api_id'],
        api_hash=account_data['api_hash'],
        phone_number=account_data['phone_number']
    )

    try:
        await callback.message.answer(text='Сейчас вам придет код для авторизации на аккаунт, который вы добавляете!\n'
                                           'Введите его:')
        # Ловим и сохраняем хэш кода авторизации для дальнейшего использования
        code_hash = await new_account.start_session()
        await state.update_data({'code_hash': code_hash, 'new_account': new_account})

        await state.set_state(AddingAccount.code_input)

    except ApiIdInvalid:
        await callback.message.answer(text='Вы ввели неверный <b>api_id или api_hash</b>!\n'
                                           'Перепроверьте все и введи заново')
        await state.set_state(AddingAccount.check_data)

    except PhoneNumberInvalid:
        await callback.message.answer(text='Вы ввели неверный <b>номер телефона</b>!\n'
                                           'Перепроверьте все и введи заново')
        await state.set_state(AddingAccount.check_data)


@dp.message(AddingAccount.code_input, F.text.regexp(r'\d{5}'))
async def auth_code_input(msg: Message, state: FSMContext):
    """Пользователь вводит код авторизации и здесь мы его ловим"""
    account_data = await state.get_data()
    await account_data['new_account'].authorization_and_start(code_hash=account_data['code_hash'], code=str(msg.text))

    account_dict[account_data['name']] = account_data['new_account']

    await msg.answer(text='Аккаунт добавлен!')
    await send_status_info(msg=msg)
    await state.clear()


@dp.message(AddingAccount.code_input, F.text != '🚫 Отмена')
async def code_error_input(msg: Message):
    """Некорректный ввод кода"""
    await msg.answer(text='Код содержит пять цифр! Повторите ввод:')


@dp.message(AddingAccount.change_name, F.text != '🚫 Отмена')
async def change_name(msg: Message, state: FSMContext):
    """Здесь мы пользователь меняет имя аккаунта"""
    await state.update_data({'name': msg.text})
    await check_the_data(msg=msg, state=state)
    await state.set_state(AddingAccount.check_data)


@dp.message(AddingAccount.change_api_id, F.text.isdigit())
async def change_api_id(msg: Message, state: FSMContext):
    """Здесь мы пользователь меняет api_id"""
    await state.update_data({'api_id': msg.text})
    await check_the_data(msg=msg, state=state)
    await state.set_state(AddingAccount.check_data)


@dp.message(AddingAccount.change_api_id, F.text != '🚫 Отмена')
@dp.message(AddingAccount.api_id_input, F.text != '🚫 Отмена')
async def api_error_input(msg: Message):
    """При не правильном вводе api_id"""
    await msg.answer(text='<b>api_id</b> состоит только из цифр! Повторите ввод')


@dp.message(AddingAccount.change_api_hash, F.text != '🚫 Отмена')
async def change_api_hash(msg: Message, state: FSMContext):
    """Здесь мы пользователь меняет api_hash"""
    await state.update_data({'api_hash': msg.text})
    await check_the_data(msg=msg, state=state)
    await state.set_state(AddingAccount.check_data)


@dp.message(AddingAccount.change_phone_number, F.text.regexp(r'\+\d{10,}'))
async def change_phone_number(msg: Message, state: FSMContext):
    """Здесь мы пользователь меняет телефонный номер"""
    await state.update_data({'phone_number': msg.text})
    await check_the_data(msg=msg, state=state)
    await state.set_state(AddingAccount.check_data)


@dp.message(AddingAccount.change_phone_number, F.text != '🚫 Отмена')
@dp.message(AddingAccount.phone_number_input, F.text != '🚫 Отмена')
async def phone_nuber_error_input(msg: Message):
    """При не правильном вводе телефонного номера"""
    await msg.answer(text='<b>Телефонный номер</b> должен быть в международном формате!\n'
                          'Пример +79221110500\nПовторите ввод!')


@dp.message(F.text == '❌ Удалить аккаунт')
async def start_remove_account(msg: Message, state: FSMContext):
    """Начало удаления аккаунта"""
    await msg.answer(text='Выберете аккаунт для удаления:', reply_markup=accounts_choice(account_dict))
    await state.set_state(AddingAccount.deletion_account)


@dp.callback_query(AddingAccount.deletion_account, F.data.startswith('ac_'))
async def ask_about_account_deletion(callback: CallbackQuery, state: FSMContext):
    """Спрашиваем подтверждение на удаление"""
    removing_acc: Account = account_dict[callback.data.replace('ac_', '')]
    await state.set_data({'account': removing_acc})
    await callback.message.answer(text='Вы уверены?', reply_markup=ask_deletion)


@dp.message(AddingAccount.deletion_account, F.text == 'Да')
async def remove_account(msg: Message, state: FSMContext):
    """Удаляем выбранный аккаунт"""
    removing_acc: Account = (await state.get_data())['account']
    await removing_acc.log_out_account()
    await msg.answer('Аккаунт удален!')
    await state.clear()
    await send_status_info(msg)


@dp.message(AddingAccount.deletion_account, F.text == 'Нет')
async def not_remove_account(msg: Message, state: FSMContext):
    """Не удаляем выбранный аккаунт"""
    await state.clear()
    await send_status_info(msg)


@dp.message(F.text == '🚫 Отмена')
async def cancel_function(msg: Message, state: FSMContext):
    """Функция отмены"""
    await state.clear()
    await send_status_info(msg)


@dp.message(Command('get_log'))
async def get_bot_log(msg: Message):
    """Команда выгружает в чат файл с логом бота"""
    log_file = FSInputFile('bot.log')
    await msg.answer_document(document=log_file)
