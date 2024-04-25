import re
import asyncio

from aiogram.utils.media_group import MediaGroupBuilder

from loader import dp
from keyboards import (main_menu, back_button, cancel_button_2, file_adding, text_adding,
                       accounts_choice, menu_for_account, chats_for_mailing_list, action_with_messages,
                       messages_for_preview, remove_message)
from utils.account_model import Account, account_dict
from .main_menu import send_status_info
from states import AccountSettings

from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram import F, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext


async def preview_account(msg: Message, account: Account):
    """Функция запускает просмотр аккаунта"""
    await msg.delete()
    await msg.answer(text='Настройки юзер бота', reply_markup=back_button)
    await msg.answer(text=account.get_account_info(), reply_markup=menu_for_account)


@dp.message(F.text == 'Подключенные аккаунты')
async def get_accounts_list(msg: Message):
    """Демонстрация всех подключенных аккаунтов"""
    await msg.answer(text='Выберете аккаунт:', reply_markup=accounts_choice(account_dict))


@dp.callback_query(F.data.startswith('ac_'))
async def open_account_settings(callback: CallbackQuery, state: FSMContext):
    """Хэндлер открывает меню для каждого конкретного аккаунта"""
    preview_acc = account_dict[callback.data.replace('ac_', '')]
    await state.set_data({'account': preview_acc})
    await state.set_state(AccountSettings.view_account)
    await preview_account(callback.message, preview_acc)


@dp.callback_query(AccountSettings.view_account, F.data == 'switch')
async def switch_account_activity(callback: CallbackQuery, state: FSMContext):
    """Переключатель для состояния активности аккаунта"""
    preview_acc = (await state.get_data())['account']
    preview_acc.change_activity()
    await preview_account(callback.message, preview_acc)


@dp.callback_query(AccountSettings.view_account, F.data == 'put_chats_list')
async def start_put_chats_list(callback: CallbackQuery, state: FSMContext):
    """Начало добавления чатов на вступление юзер бота"""
    await state.set_state(AccountSettings.put_chats)
    await callback.message.delete()
    await callback.message.answer(text='Введите ссылку на группу:', reply_markup=back_button)


@dp.message(AccountSettings.put_chats, F.text != 'Назад')
async def put_chats(msg: Message, state: FSMContext):
    """Запуск попытки юзер бота вступить в группу"""
    preview_acc = (await state.get_data())['account']
    try:
        chat_obj = await preview_acc.join_to_chat(chat=msg.text)
        await msg.answer('Чат добавлен')
    except:
        await msg.answer('Что-то пошло не так')


@dp.callback_query(AccountSettings.view_account, F.data == 'chats_for_mailing')
async def chat_for_mailing_menu(callback: CallbackQuery, state: FSMContext):
    """Здесь мы открываем меню для настройки чатов для рассылки"""
    preview_acc = (await state.get_data())['account']

    # Проверим, состоит ли юзер бот хоть в одном чате
    if len(preview_acc.get_chats_dict()) > 0:
        await callback.message.delete()
        await callback.message.answer(text='Выберете чат для настройки', reply_markup=chats_for_mailing_list(
            chats_dict=preview_acc.get_chats_dict()
        ))
        await state.set_state(AccountSettings.chats_for_mailing)
    else:
        await callback.message.answer('Данный юзер бот пока не состоит ни водном чате!')


@dp.callback_query(AccountSettings.view_account, F.data == 'msg_for_mailing')
async def messages_for_mailing_menu(callback: CallbackQuery, state: FSMContext):
    """Даем пользователю выбрать действия для сообщений"""
    await callback.message.edit_reply_markup(reply_markup=action_with_messages)


@dp.callback_query(AccountSettings.view_account, F.data == 'add_msg')
async def start_adding_message_for_mailing(callback: CallbackQuery, state: FSMContext):
    """Начинаем добавление сообщений для рассылки"""
    await callback.message.delete()
    await callback.message.answer(text='Введите <b>название</b> сообщения:', reply_markup=cancel_button_2)
    await state.set_state(AccountSettings.msg_title)


@dp.message(AccountSettings.msg_title, F.text != 'Отмена')
async def set_message_title(msg: Message, state: FSMContext):
    """Ловим название для сообщения и приглашение на ввод основного текста"""
    await state.update_data({'msg_title': msg.text})
    msg_text = (f'Сообщение может быть трех видов:\n'
                f'- только текст (3000 символов)\n'
                f'- текст (1024 символа, видеосообщение не может содержать текст) '
                f'+ файл(ы)(до 10 файлов, если это фото, видео, документы или аудиофайлы)\n'
                f'- только файл(ы)(до 10 файлов)\n\n'
                f'Скиньте файл(ы) и/или нажмите кнопку <b>Дальше</b>')
    await msg.answer(text=msg_text, reply_markup=file_adding)
    await state.update_data({'mediafile': []})
    await state.set_state(AccountSettings.msg_files)


@dp.message(AccountSettings.msg_files, F.text != 'Дальше')
async def adding_files(msg: Message, state: FSMContext):
    """Ловим медиафайлы"""
    # Так как, при скидывании более одного файла, бот воспринимает это сразу как несколько отдельных
    # сообщений, то будем использовать эту причудливую конструкцию с заранее созданным списком

    file_id_list = (await state.get_data())['mediafile']

    if msg.photo:
        file_id_list.append((msg.photo[-1].file_id, 'photo'))
    elif msg.video:
        file_id_list.append((msg.video.file_id, 'video'))
    elif msg.document:
        file_id_list.append((msg.document.file_id, 'document'))
    elif msg.video_note:
        file_id_list = [(msg.video_note.file_id, 'video_note')]
    elif msg.audio:
        file_id_list.append((msg.audio.file_id, 'audio'))
    elif msg.voice:
        file_id_list = [(msg.voice.file_id, 'voice')]

    await state.update_data({'mediafile': file_id_list})


@dp.message(AccountSettings.msg_files, F.text == 'Дальше')
async def check_files(msg: Message, state: FSMContext):
    """Проверяем файлы, которые скинул пользователь. Если все нормально, то предлагаем ввести текст"""
    file_id_list = (await state.get_data())['mediafile']

    # Если файлов больше чем надо, то просим повторить
    if 0 < len(file_id_list) <= 10:
        type_set = {t[1] for t in file_id_list}

        # Проверяем на однотипность добавленных файлов. Вперемешку могут быть только фото и видео(не видеосообщение)

        if len(type_set) == 1:  # значит, что у передаваемых файлов один тип
            await msg.answer(text='Теперь введите текст или нажмите кнопу Готово:', reply_markup=text_adding)
            await state.set_state(AccountSettings.msg_text)
            await state.update_data({'only_text': False})
        elif len(type_set) == 2 and ('photo' and 'video' in type_set):
            await msg.answer(text='Теперь введите текст или нажмите кнопу Готово:', reply_markup=text_adding)
            await state.set_state(AccountSettings.msg_text)
            await state.update_data({'only_text': False})
        else:
            await msg.answer(text='Файлы должны быть однотипными! Совместно можно только фото и видео!',
                             reply_markup=file_adding)
            await state.update_data({'mediafile': []})

    elif len(file_id_list) == 0:  # Значит только текст
        await state.set_state(AccountSettings.msg_text)
        await msg.answer(text='Введите текст', reply_markup=cancel_button_2)
        await state.update_data({'only_text': True})

    else:
        await msg.answer(text='Фалов слишком много, повторите попытку', reply_markup=file_adding)
        await state.update_data({'mediafile': []})


@dp.message(AccountSettings.msg_text, F.text != 'Отменить')
async def message_text_input(msg: Message, state: FSMContext):
    """Ловим текст сообщения и/или заканчиваем ввод сообщения для рассылки"""
    if '<' in msg.text:
        await msg.answer(text=html.quote('Использование символа "<" в тексте нельзя, так как это нарушит работу бота!'))
    else:

        message_info = await state.get_data()
        enti = msg.entities  # Для ссылок внутри текста
        text_for_post = msg.text
        try:
            for elem in enti:
                if elem.type == 'text_link':
                    reg = r'[^#]{0}'.format(elem.extract_from(msg.text))
                    sub_str = f'<a href = "{elem.url}">{elem.extract_from(msg.text)}</a>'
                    text_for_post = re.sub(reg, sub_str, text_for_post)
        except TypeError:
            pass

        if message_info['only_text']:
            if len(msg.text) <= 3000:
                message_info['account'].set_message_for_mailing(message={
                    message_info['msg_title']: text_for_post
                })
                await msg.answer(text='Добавлено')
                preview_acc = message_info['account']
                await preview_account(msg, preview_acc)
                await state.set_state(AccountSettings.view_account)
                # await state.clear()
            else:
                await state.set_state(AccountSettings.false_state)
                # Это нужно для того, что бы когда телеграмм разобьет
                # сообщение на две части не пропустить второе

                await msg.answer(text=f'Ограничение для одного сообщения 3000 символов '
                                      f'(Вы ввели {len(msg.text)} символа)',
                                 reply_markup=text_adding)

                await asyncio.sleep(1)
                await state.set_state(AccountSettings.msg_text)  # И сразу установим стэйт обратно,
                # что бы пользователь мог повторить ввод текста для публикации
        else:
            if len(msg.text) <= 1024:
                message_info['account'].set_message_for_mailing(message={
                    message_info['msg_title']: (
                    text_for_post if msg.text != 'Готово' else None, message_info['mediafile'])
                })
                await msg.answer(text='Добавлено')
                preview_acc = message_info['account']
                await preview_account(msg, preview_acc)
                await state.set_state(AccountSettings.view_account)

            else:
                await msg.answer(text=f'Ограничение для описания файла(ов) 1024 символа '
                                      f'(Вы ввели {len(msg.text)} символа)',
                                 reply_markup=text_adding)


@dp.callback_query(AccountSettings.view_account, F.data == 'preview_msg')
async def start_preview_messages_and_remove(callback: CallbackQuery, state: FSMContext):
    """Начинаем просмотр списка добавленных сообщений для рассылки"""
    await callback.message.delete()
    bot_mess_dict = (await state.get_data())['account'].get_messages_dict()
    await callback.message.answer(text='Выберете сообщение для просмотра:',
                                  reply_markup=messages_for_preview(bot_mess_dict))
    await state.set_state(AccountSettings.preview_mess)


@dp.callback_query(AccountSettings.preview_mess, F.data.startswith('mess_'))
async def preview_message_and_remove(callback: CallbackQuery, state: FSMContext):
    """Показываем сообщение и даем возможность удалить"""

    # У выбранного аккаунта вызываем словарь с сообщениями, а ключ для него достаем из callback
    message_self = (await state.get_data())['account'].get_messages_dict()[callback.data.replace('mess_', '')]
    await callback.message.delete()
    await callback.message.answer(text='Предпросмотр', reply_markup=remove_message)
    await state.set_state(AccountSettings.msg_preview)

    if isinstance(message_self, str):  # значит объявление без медиафайлов

        await callback.message.answer(text=message_self)

    else:
        if message_self[1][0][1] in {'photo', 'video', 'audio', 'document'}:
            # Так как только эти типы файлов могут быть медиа группой
            media_group = MediaGroupBuilder(caption=message_self[0])
            for mediafile in message_self[1]:
                media_group.add(type=mediafile[1], media=mediafile[0])

            await callback.message.answer_media_group(media=media_group.build())

        else:  # voice, video_note
            if message_self[1][0][1] == 'voice':
                await callback.message.answer_voice(voice=message_self[1][0][0],
                                     caption=message_self[0], protect_content=True)
            elif message_self[1][0][1] == 'video_note':
                await callback.message.answer_video_note(video_note=message_self[1][0][0])


# @dp.message(AccountSettings.msg_body, F.text != 'Отмена')
# async def set_message_body(msg: Message, state: FSMContext):
#     """Ловим само сообщение"""
#     await state.update_data({'msg_body': msg.text})
@dp.message(AccountSettings.msg_preview, F.text == 'Назад')
async def return_to_mess_list(msg: Message, state: FSMContext):
    """Из просмотра сообщения назад к списку сообщений"""
    bot_mess_dict = (await state.get_data())['account'].get_messages_dict()
    await msg.answer(text='Назад к списку сообщений', reply_markup=back_button)
    await msg.answer(text='Выберете сообщение для просмотра:',
                     reply_markup=messages_for_preview(bot_mess_dict))
    await state.set_state(AccountSettings.preview_mess)


@dp.message(AccountSettings.preview_mess, F.text == 'Назад')
@dp.message(AccountSettings.view_account, F.text == 'Отменить')
@dp.message(AccountSettings.msg_files, F.text == 'Отменить')
@dp.message(AccountSettings.msg_text, F.text == 'Отменить')
@dp.message(AccountSettings.msg_title, F.text == 'Отменить')
@dp.message(AccountSettings.chats_for_mailing, F.text == 'Назад')
@dp.message(AccountSettings.put_chats, F.text == 'Назад')
async def back_to_account_preview(msg: Message, state: FSMContext):
    """Возвращение к просмотру юзер бота"""
    preview_acc = (await state.get_data())['account']
    await preview_account(msg, preview_acc)
    await state.set_state(AccountSettings.view_account)


@dp.message(AccountSettings.view_account, F.text == 'Назад')
async def back_to_account_list(msg: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await get_accounts_list(msg)


@dp.message(F.text == 'Назад')
async def back_to_main_menu(msg: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await send_status_info(msg)
    