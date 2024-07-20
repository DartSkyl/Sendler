import re
import asyncio

from aiogram.utils.media_group import MediaGroupBuilder

from loader import dp
from keyboards import (back_button, cancel_button_2, file_adding, text_adding,
                       accounts_choice, menu_for_account, mailing_sett, action_with_messages,
                       messages_for_preview, remove_message, messages_for_removing, ask_deletion)
from utils.account_model import Account, account_dict
from .main_menu import send_status_info
from states import AccountSettings

from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram import F, html
from aiogram.fsm.context import FSMContext
from pyrogram.errors.exceptions.bad_request_400 import (UsernameInvalid, UserAlreadyParticipant,
                                                        InviteHashExpired, UsernameNotOccupied)
from pyrogram.errors.exceptions.flood_420 import FloodWait


async def preview_account(msg: Message, account: Account):
    """Функция запускает просмотр аккаунта"""
    await msg.delete()
    await msg.answer(text='Настройки юзер бота', reply_markup=back_button)
    await msg.answer(text=account.get_account_info(), reply_markup=menu_for_account)


@dp.message(F.text == '📋 Подключенные аккаунты')
async def get_accounts_list(msg: Message):
    """Демонстрация всех подключенных аккаунтов"""
    await msg.answer(text='Выберете аккаунт:', reply_markup=accounts_choice(account_dict))


@dp.callback_query(F.data.startswith('ac_'))
async def open_account_settings(callback: CallbackQuery, state: FSMContext):
    """Хэндлер открывает меню для каждого конкретного аккаунта"""
    preview_acc: Account = account_dict[callback.data.replace('ac_', '')]
    await state.set_data({'account': preview_acc})
    await state.set_state(AccountSettings.view_account)
    await preview_account(callback.message, preview_acc)


@dp.callback_query(AccountSettings.view_account, F.data == 'switch')
async def switch_account_activity(callback: CallbackQuery, state: FSMContext):
    """Переключатель для состояния активности аккаунта"""
    preview_acc: Account = (await state.get_data())['account']

    try:
        await preview_acc.change_activity()
        await preview_account(callback.message, preview_acc)
    except ValueError:
        await callback.message.answer('Установите хотя бы одно сообщение для рассылки!')
        await callback.answer()
    except IndexError:
        await callback.message.answer('Установите Интервал для рассылки!')
        await callback.answer()
    except ZeroDivisionError:
        await callback.message.answer('Установите список чатов для рассылки!')
        await callback.answer()


@dp.callback_query(AccountSettings.view_account, F.data == 'put_chats_list')
async def start_put_chats_list(callback: CallbackQuery, state: FSMContext):
    """Начало добавления чатов на вступление юзер бота"""
    preview_acc: Account = (await state.get_data())['account']

    if preview_acc.get_active():
        await callback.answer()
        await callback.message.answer('<b>Сначала остановите рассылку❗</b>')
    else:
        await state.set_state(AccountSettings.put_chats)
        await callback.message.delete()
        await callback.message.answer(text='Введите список ссылок на группы:', reply_markup=back_button)


@dp.message(AccountSettings.put_chats, F.text != '◀️ Назад')
async def put_chats(msg: Message, state: FSMContext):
    """Запуск цикла вступления юзер бота в группы. Конструкция в основном состоит из блоков try except
    По неведомым причинам, вступать в открытые чаты можно только через юзернэйм группы. Отсюда и дополнительная
    ветка try except. Из опасности флуда всю конструкцию пришлось обернуть в цикл while. Так как в ином случае,
    пришлось увеличивать ветки try except до бесконечности. По крайней мере, я так вижу. У вас может получиться лучше"""
    preview_acc: Account = (await state.get_data())['account']

    # Предварительно зачищаем уже установленные чаты
    preview_acc.chats_dict_clean()

    chats_links = msg.text.split('\n')
    await msg.answer('<b>Начата процедура добавления чатов!</b>')

    # Когда выстрелит флуд, то по сути придется все делать заново.
    # Что бы этого избежать то при каждом успешном добавлении удаляем
    # из списка со ссылками на группы уже отработанные. И когда придет флуд,
    # просто продолжим с оставшимися ссылками.

    while len(chats_links) > 0:
        for link in chats_links:
            try:
                await preview_acc.join_to_chat(chat=link)
                await msg.answer(f'Чат добавлен!\n{link}')
                chats_links.remove(link)
            except UsernameInvalid:
                try:
                    await preview_acc.join_to_chat(chat=link.replace('https://t.me/', ''))
                    await msg.answer(f'Чат добавлен!\n{link}')
                    chats_links.remove(link)
                except UsernameInvalid:
                    await msg.answer(f'Неверная ссылка!\n{link}')
                    chats_links.remove(link)
                except UsernameNotOccupied:
                    await msg.answer(f'Неверная ссылка!\n{link}')
                    chats_links.remove(link)
                except UserAlreadyParticipant:
                    await msg.answer(f'Юзер бот уже состоит в данном чате!\n{link}')
                    await preview_acc.add_chat_info(chat=link.replace('https://t.me/', ''))
                    chats_links.remove(link)
                except InviteHashExpired:
                    await msg.answer(f'Юзер бот заблокирован в данном чате или '
                                     f'ссылка уже не действительна!\n{link}')
                    chats_links.remove(link)
                except FloodWait as exc:
                    await msg.answer(f'❗Телеграм ругается на флуд❗\n'
                                     f'Перерыв {exc.value} секунд')
                    await asyncio.sleep(5)  # Подождем дополнительно. Прибавить не решился, так как фиг его знает
                    await asyncio.sleep(exc.value)
                except KeyError:
                    await msg.answer(f'Юзер бот заблокирован в данном чате или '
                                     f'ссылка уже не действительна!\n{link}')
                    chats_links.remove(link)
            except UserAlreadyParticipant:
                await msg.answer(f'Юзер бот уже состоит в данном чате!\n{link}')
                await preview_acc.add_chat_info(chat=link)
                chats_links.remove(link)
            except InviteHashExpired:
                await msg.answer(f'Юзер бот заблокирован в данном чате или '
                                 f'ссылка уже не действительна!\n{link}')
                chats_links.remove(link)
            except UsernameNotOccupied:
                await msg.answer(f'Неверная ссылка!\n{link}')
                chats_links.remove(link)
            except FloodWait as exc:
                await msg.answer(f'❗Телеграм ругается на флуд❗\n'
                                 f'Перерыв {exc.value} секунд')
                await asyncio.sleep(5)  # Подождем дополнительно. Прибавить не решился, так как фиг его знает
                await asyncio.sleep(exc.value)
    await msg.answer('<b>Добавление чатов завершено</b>')
    await preview_account(msg, preview_acc)
    await state.set_state(AccountSettings.view_account)


@dp.callback_query(AccountSettings.view_account, F.data == 'mailing_settings')
async def settings_for_mailing_menu(
        callback: CallbackQuery | None = None,
        state: FSMContext | None = None,
        msg: Message | None = None
):
    """Здесь мы открываем меню для настройки рассылки"""
    preview_acc: Account = (await state.get_data())['account']
    chats = preview_acc.get_chats_dict()
    settings_dict = preview_acc.get_settings_dict()

    # Проверим, состоит ли юзер бот хоть в одном чате
    msg_text = 'Чаты, в которых состоит бот:\n\n' if len(chats) > 0 \
        else 'Данный юзер бот пока не состоит ни в одном чате!\n'

    # Если пусто, то сами понимаете...
    for link in chats.keys():
        msg_text += link + '\n'

    msg_text += '\n<b>Интервал:</b> ' + (f'{settings_dict["interval"]} мин' if settings_dict["interval"]
                                         else 'Не установлен')

    msg_text += '\n\n<b>Установленные сообщения:</b>\n'

    if len(settings_dict['messages']) > 0:
        for mes in settings_dict['messages']:
            msg_text += mes + '\n'
    else:
        msg_text += '<i>-Отсутствуют-</i>'
    if callback:
        await callback.message.delete()
        await callback.message.answer(text=msg_text, reply_markup=mailing_sett)
        await state.set_state(AccountSettings.mailing_settings)
    else:
        await msg.answer(text=msg_text, reply_markup=mailing_sett)
        await state.set_state(AccountSettings.mailing_settings)


@dp.callback_query(AccountSettings.mailing_settings, F.data == 'interval')
async def setup_interval(callback: CallbackQuery, state: FSMContext):
    """Переходим к установке интервала рассылки"""
    await callback.message.delete()
    await callback.message.answer(text='Введите желаемый интервал в минутах:', reply_markup=cancel_button_2)
    await state.set_state(AccountSettings.setup_interval)


@dp.message(AccountSettings.setup_interval, F.text.regexp(r'\d{1,}'))
async def catch_interval(msg: Message, state: FSMContext):
    """Ловим значение интервала в минутах"""
    preview_acc: Account = (await state.get_data())['account']
    preview_acc.set_interval(int(msg.text))
    await msg.answer(text=f'<b>Установлен интервал {msg.text} мин</b>', reply_markup=back_button)

    # И возвращаемся в меню настроек

    await settings_for_mailing_menu(state=state, msg=msg)


@dp.callback_query(AccountSettings.mailing_settings, F.data == 'add_mess')
async def setup_messages_for_mailing(callback: CallbackQuery, state: FSMContext):
    """Переходим к установке сообщений для рассылки из общего словаря с сообщениями"""
    bot_mess_dict = (await state.get_data())['account'].get_messages_dict()
    await callback.message.delete()
    await callback.message.answer('Выберете сообщение из списка:', reply_markup=messages_for_preview(bot_mess_dict))
    await state.set_state(AccountSettings.setup_message)


@dp.callback_query(AccountSettings.setup_message, F.data.startswith('mess_'))
async def catch_message(callback: CallbackQuery, state: FSMContext):
    """Ловим сообщение для добавления в рассылку"""
    preview_acc: Account = (await state.get_data())['account']

    # Вынимаем название сообщения прямо из callback
    preview_acc.setup_mess_in_settings_dict(callback.data.replace('mess_', ''))

    # И возвращаемся в меню настройки рассылки

    await settings_for_mailing_menu(state=state, callback=callback)


@dp.callback_query(AccountSettings.mailing_settings, F.data == 'del_mess')
async def remove_message_from_setting(callback: CallbackQuery, state: FSMContext):
    """Переходим к удалению сообщения из настроек рассылки"""

    # Метод возвращает множество
    bot_mess_set = (await state.get_data())['account'].get_messages_from_settings()
    await callback.message.delete()
    await callback.message.answer(text='Выберете какое сообщение удалить:',
                                  reply_markup=messages_for_removing(bot_mess_set))
    await state.set_state(AccountSettings.delete_msg_from_settings)


@dp.callback_query(AccountSettings.delete_msg_from_settings, F.data.startswith('rem_'))
async def catch_removing_messages(callback: CallbackQuery, state: FSMContext):
    """Ловим удаляемое сообщение"""
    preview_acc: Account = (await state.get_data())['account']

    # Вынимаем название сообщения прямо из callback

    preview_acc.remove_message_from_settings(callback.data.replace('rem_', ''))

    # И возвращаемся в меню настройки рассылки

    await settings_for_mailing_menu(state=state, callback=callback)


@dp.callback_query(AccountSettings.view_account, F.data == 'msg_for_mailing')
async def messages_for_mailing_menu(callback: CallbackQuery, state: FSMContext):
    """Даем пользователю выбрать действия для сообщений"""
    await callback.message.edit_reply_markup(reply_markup=action_with_messages)
    await state.set_state(AccountSettings.choice_msg_action)


@dp.callback_query(AccountSettings.choice_msg_action, F.data == 'add_msg')
async def start_adding_message_for_mailing(callback: CallbackQuery, state: FSMContext):
    """Начинаем добавление сообщений для рассылки"""
    await callback.message.delete()
    await callback.message.answer(text='Введите <b>название</b> сообщения:', reply_markup=cancel_button_2)
    await state.set_state(AccountSettings.msg_title)


@dp.message(AccountSettings.msg_title, F.text != '🚫 Отменить')
async def set_message_title(msg: Message, state: FSMContext):
    """Ловим название для сообщения и приглашение на ввод основного текста"""
    await state.update_data({'msg_title': msg.text})
    msg_text = (f'Сообщение может быть трех видов:\n'
                f'- только текст (3000 символов)\n'
                f'- текст (1024 символа, видеосообщение не может содержать текст) '
                f'+ файл(ы)(до 10 файлов, если это фото, видео, документы или аудиофайлы)\n'
                f'- только файл(ы)(до 10 файлов)\n\n'
                f'‼️<b>Скидывать можно только файлы которые хранятся на ваше компьютере в виде абсолютных путей.'
                f'Так же, через пробел указать тип файла - photo, video, document, audio.</b>‼️\n\n'
                f'Можно скинуть список, где каждый файл указан с новой строки!\n'
                f'Скиньте файл(ы) и/или нажмите кнопку <b>Дальше</b>')
    await msg.answer(text=msg_text, reply_markup=file_adding)
    await state.update_data({'mediafile': []})
    await state.set_state(AccountSettings.msg_files)


@dp.message(AccountSettings.msg_files, F.text != 'Дальше ▶️', F.text != '🚫 Отменить')
async def adding_files(msg: Message, state: FSMContext):
    """Ловим медиафайлы"""
    # Так как, при скидывании более одного файла может быть несколько отдельных
    # сообщений, то будем использовать эту причудливую конструкцию с заранее созданным списком
    file_list = (await state.get_data())['mediafile']

    files = msg.text.split('\n')
    for file in files:
        file = file.replace('"', '').split()
        # если вдруг в пути будет лишний пробел
        file = [' '.join(file[0:-1]), file[-1]]
        if file[1] in {'photo', 'video', 'document', 'audio'}:
            file_list.append(file)

            await msg.answer('Файл добавлен. Скиньте еще или нажмите кнопку дальше')
        else:
            await msg.answer('Тип файла указан не верно!')
    else:
        await state.update_data({'mediafile': file_list})


@dp.message(AccountSettings.msg_files, F.text == 'Дальше ▶️')
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


@dp.message(AccountSettings.msg_text, F.text != '🚫 Отменить')
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
                preview_acc: Account = message_info['account']
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
                preview_acc: Account = message_info['account']
                await preview_account(msg, preview_acc)
                await state.set_state(AccountSettings.view_account)

            else:
                await msg.answer(text=f'Ограничение для описания файла(ов) 1024 символа '
                                      f'(Вы ввели {len(msg.text)} символа)',
                                 reply_markup=text_adding)


@dp.callback_query(AccountSettings.choice_msg_action, F.data == 'preview_msg')
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

    # Сохраним название для возможного удаления
    await state.update_data({'title_for_del': callback.data.replace('mess_', '')})
    await callback.message.delete()
    await callback.message.answer(text='Предпросмотр',
                                  reply_markup=remove_message
                                  )
    await state.set_state(AccountSettings.msg_preview)

    if isinstance(message_self, str):  # значит объявление без медиафайлов

        await callback.message.answer(text=message_self)

    else:

        media_group = MediaGroupBuilder(caption=message_self[0])
        for mediafile in message_self[1]:
            media_group.add(type=mediafile[1], media=FSInputFile(mediafile[0]))

        await callback.message.answer_media_group(media=media_group.build())


@dp.message(AccountSettings.msg_preview, F.text == 'Удалить')
async def ask_about_deletion(msg: Message, state: FSMContext):
    """Просим подтвердить удаление"""
    await msg.answer(text='Вы уверены?', reply_markup=ask_deletion)
    await state.set_state(AccountSettings.remove_mess)


@dp.message(AccountSettings.remove_mess, F.text == 'Да')
async def remove_message_func(msg: Message, state: FSMContext):
    """Удаляем выбранное сообщения из словаря со всеми сообщениями"""
    all_data = await state.get_data()  # Так просто удобней
    pre_account: Account = all_data['account']
    del_message = all_data['title_for_del']
    pre_account.remove_message_from_dict(del_message)

    # И возвращаемся к списку сообщений

    bot_mess_dict = pre_account.get_messages_dict()
    await msg.answer('<b>Сообщение удалено!</b>')
    await msg.answer(text='Назад к списку сообщений', reply_markup=back_button)
    await msg.answer(text='Выберете сообщение для просмотра:',
                     reply_markup=messages_for_preview(bot_mess_dict))
    await state.set_state(AccountSettings.preview_mess)


@dp.message(AccountSettings.remove_mess, F.text == 'Нет')
async def else_not_delete(msg: Message, state: FSMContext):
    """Если не удаляем сообщение"""
    bot_mess_dict = (await state.get_data())['account'].get_messages_dict()
    await msg.answer(text='Назад к списку сообщений', reply_markup=back_button)
    await msg.answer(text='Выберете сообщение для просмотра:',
                     reply_markup=messages_for_preview(bot_mess_dict))
    await state.set_state(AccountSettings.preview_mess)


@dp.message(AccountSettings.msg_preview, F.text == '◀️ Назад')
async def return_to_mess_list(msg: Message, state: FSMContext):
    """Из просмотра сообщения назад к списку сообщений"""
    bot_mess_dict = (await state.get_data())['account'].get_messages_dict()
    await msg.answer(text='Назад к списку сообщений', reply_markup=back_button)
    await msg.answer(text='Выберете сообщение для просмотра:',
                     reply_markup=messages_for_preview(bot_mess_dict))
    await state.set_state(AccountSettings.preview_mess)


@dp.message(AccountSettings.setup_interval, F.text == '🚫 Отменить')
@dp.message(AccountSettings.setup_message, F.text.in_({'🚫 Отменить', '◀️ Назад'}))
@dp.message(AccountSettings.delete_msg_from_settings, F.text.in_({'🚫 Отменить', '◀️ Назад'}))
async def back_to_settings_menu(msg: Message, state: FSMContext):
    """Назад в меню настроек рассылки"""
    await settings_for_mailing_menu(msg=msg, state=state)


@dp.message(AccountSettings.preview_mess, F.text.in_({'🚫 Отменить', '◀️ Назад'}))
@dp.message(AccountSettings.choice_msg_action, F.text.in_({'🚫 Отменить', '◀️ Назад'}))
@dp.message(AccountSettings.msg_files, F.text.in_({'🚫 Отменить', '◀️ Назад'}))
@dp.message(AccountSettings.msg_text, F.text.in_({'🚫 Отменить', '◀️ Назад'}))
@dp.message(AccountSettings.msg_title, F.text.in_({'🚫 Отменить', '◀️ Назад'}))
@dp.message(AccountSettings.mailing_settings, F.text.in_({'🚫 Отменить', '◀️ Назад'}))
@dp.message(AccountSettings.put_chats, F.text.in_({'🚫 Отменить', '◀️ Назад'}))
async def back_to_account_preview(msg: Message, state: FSMContext):
    """Возвращение к просмотру юзер бота"""
    preview_acc: Account = (await state.get_data())['account']
    await preview_account(msg, preview_acc)
    await state.set_state(AccountSettings.view_account)


@dp.message(AccountSettings.view_account, F.text.in_({'🚫 Отменить', '◀️ Назад'}))
async def back_to_account_list(msg: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await get_accounts_list(msg)


@dp.message(F.text.in_({'🚫 Отменить', '◀️ Назад'}))
async def back_to_main_menu(msg: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await send_status_info(msg)
