import random
import os
import asyncio
from .mailing_core import MailingCore
from pyrogram import Client
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate
from pyrogram.errors.exceptions.flood_420 import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid


# Все подключенные аккаунты будем хранить в словаре, гле ключ это имя бот, а значение сам бот
account_dict = dict()

publisher = None


async def create_publisher():
    global publisher
    publisher = MailingCore()


class Account:
    def __init__(self, name: str, api_id: int, api_hash: str, phone_number: str):
        self._name = name
        self._api_id = api_id
        self._api_hash = api_hash
        self._phone_number = phone_number
        self._client = Client(name=f'{name}', api_id=api_id, api_hash=api_hash, phone_number=phone_number)
        self._active = False
        self._mute = False
        self._chat_dict = dict()  # Ключ это название группы, значение это ID группы
        self._msg_dict = dict()  # Ключ это название сообщения, значение это само сообщение
        # В словаре с настройками для рассылки будем хранить интервал рассылки и множество с сообщениями
        self._mailing_settings = {'interval': None, 'messages': set()}

    async def start_session(self):
        """Здесь происходит авторизация аккаунта. Запрашиваем код и возвращаем хэш кода"""
        await self._client.connect()
        code_info = await self._client.send_code(self._phone_number)
        return code_info.phone_code_hash

    async def authorization_and_start(self, code_hash: str, code: str):
        """Здесь заканчиваем авторизацию и запускаемся"""
        await self._client.sign_in(phone_number=self._phone_number, phone_code_hash=code_hash, phone_code=code)
        await self._client.disconnect()
        await self._client.start()

    async def change_activity(self):
        """Метод меняет состояние активности аккаунта"""
        if self._active:
            self._active = False
            await publisher.stop_mailing(self._name)
        else:
            if len(self._chat_dict) > 0:
                if self._mailing_settings['interval']:
                    if len(self._mailing_settings['messages']) > 0:
                        self._active = True
                        await publisher.add_mailing_job(
                            interval=self._mailing_settings['interval'],
                            mailing=self.mailing_function,
                            user_bot_name=self._name
                        )
                    else:
                        raise ValueError
                else:
                    raise IndexError
            else:
                raise ZeroDivisionError

    async def join_to_chat(self, chat: str | int):
        """Метод добавления в чат. Возвращаем объект чата"""
        chat_info = await self._client.join_chat(chat_id=chat)
        chat = chat if 'https://t.me/' in chat else 'https://t.me/' + chat
        self._chat_dict[chat] = chat_info.id

# ========== Методы манипуляций информацией ==========
    def change_mute(self):
        """Меняем состояние мута"""
        if self._mute:
            self._mute = False
        else:
            self._mute = True

    def chats_dict_clean(self):
        """Очищаем словарь с чатами"""
        self._chat_dict = {}

    async def add_chat_info(self, chat):
        """Это метод, на случай, если в список добавляемых чатов, попал чат, в котором юзер бот уже состоит.
        В таком случае просто добавим необходимую информацию в словарь с чатами"""
        chat_info = await self._client.get_chat(chat_id=chat)
        chat = chat if 'https://t.me/' in chat else 'https://t.me/' + chat
        self._chat_dict[chat] = chat_info.id

    def set_interval(self, interval: int):
        """Устанавливаем значение интервала в словарь настроек"""
        self._mailing_settings['interval'] = interval

    def set_message_for_mailing(self, message: dict):
        """Передаем сюда словарь с сообщением и вливаем его в основной"""
        self._msg_dict.update(message)

    def remove_message_from_dict(self, mess_title: str):
        """Удаляем сообщение из словаря с сообщениями"""
        self._msg_dict.pop(mess_title)
        # Так же, если это сообщение есть в настройках рассылки, то его тоже следует удалить во избежание эксцессов
        try:
            self._mailing_settings['messages'].remove(mess_title)
        except KeyError:
            pass

    def remove_message_from_settings(self, mess_title: str):
        """Удаляем сообщение из настроек рассылки"""
        self._mailing_settings['messages'].remove(mess_title)

    def setup_mess_in_settings_dict(self, mess_title: str):
        """Устанавливаем сообщения в настройки рассылки"""
        self._mailing_settings['messages'].add(mess_title)

# ========== Методы получения информации об аккаунте ==========
    def get_messages_from_settings(self):
        """Возвращает сообщения добавленные в настройки рассылки"""
        return self._mailing_settings['messages']

    def get_messages_dict(self):
        """Возвращает словарь сообщений для рассылки"""
        return self._msg_dict

    def get_settings_dict(self):
        """Возвращает словарь настроек"""
        return self._mailing_settings

    def get_active(self):
        """Возвращает статус аккаунта"""
        return self._active

    def get_chats_dict(self):
        """Возвращает словарь с чатами в которых состоит юзер бот"""
        return self._chat_dict

    def get_name(self):
        """Возвращает название аккаунта"""
        return self._name

    def get_account_info(self):
        """Возвращает строку состояния аккаунта"""
        info_string = (f'Название юзер-бота: <b>{self._name}</b>\n\n'
                       f'<b>Состояние:</b> <i>{"✅ Активен" if self._active else "⛔ Неактивен"}</i>\n'
                       f'<b>Мут:</b> <i>{"⛔ Временно приостановлен" if self._mute else "✅ Нету" }</i>\n'
                       f'<b>На сколько чатов рассылает:</b> <i>{len(self._chat_dict)}</i>')
        return info_string

    async def log_out_account(self):
        """Выходим из аккаунта и удаляем из словаря"""
        await self._client.log_out()
        account_dict.pop(self._name)

    async def mailing_function(self):
        """Основная функция рассылки сообщений. Сделана внутриклассовой, что бы иметь динамичный доступ
        к сообщениям из словаря настроек и основного словаря сообщений. Что бы при изменении в этих словарях
        нигде ничего лишний раз не дергать"""

        chats_banned = []  # Если бота забанят, то сюда скинем эти чаты, а в конце цикла почистим от них словарь

        for chat_url, chat_id in self._chat_dict.items():

            files_type = {
                'photo': InputMediaPhoto,
                'video': InputMediaVideo,
                'audio': InputMediaAudio,
                'document': InputMediaDocument
            }

            # Сообщение для рассылки будем выбирать случайным образом. Так как в словаре с
            # настройками хранятся ключи от сообщений в словаре с сообщениями,
            # то преобразуя множество из словаря с настройками в список с ключами выбираем случайный ключ.
            # И по этому ключу вытаскиваем сообщение из основного словаря сообщений

            message_for_mailing = self._msg_dict[random.choice(list(self._mailing_settings['messages']))]

            # Если есть файлы, то получим список списков [file_id, file_type], иначе None
            message_file_id = message_for_mailing[1] if isinstance(message_for_mailing, tuple) else None

            try:
                if message_file_id:

                    files = [files_type[mediafile[1]](mediafile[0], caption=message_for_mailing[0])
                             for mediafile in message_file_id]

                    await self._client.send_media_group(chat_id=chat_id, media=files)

                else:
                    await self._client.send_message(chat_id=chat_id, text=message_for_mailing)
            except ChannelPrivate or PeerIdInvalid:
                # Если юзер бота забанят во время рассылки, то сохраним этот чат до конца рассылки,
                # а потом просто удалим этот чат из словаря
                chats_banned.append(chat_url)

            except FloodWait as e:
                self.change_mute()
                await asyncio.sleep(5)  # Подождем дополнительно. Прибавить не решился, так как фиг его знает)))
                await asyncio.sleep(e.value)
                self.change_mute()
            await asyncio.sleep(60)

        # Чистимся от забаненых чатов
        for url in chats_banned:
            self._chat_dict.pop(url)
