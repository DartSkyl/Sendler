from pyrogram import Client


# Все подключенные аккаунты будем хранить в словаре, гле ключ это имя бот, а значение сам бот
account_dict = dict()


class Account:
    def __init__(self, name: str, api_id: int, api_hash: str, phone_number: str):
        self._name = name
        self._api_id = api_id
        self._api_hash = api_hash
        self._phone_number = phone_number
        self._client = Client(name=f'{name}', api_id=api_id, api_hash=api_hash, phone_number=phone_number)
        self._active = False
        self._chat_dict = dict()  # Ключ это название группы, значение это ID группы
        self._msg_dict = dict()  # Ключ это название сообщения, значение это само сообщение
        # В словаре с настройками для рассылки будем хранить интервал рассылки и список с сообщениями
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

    def change_activity(self):
        """Метод меняет состояние активности аккаунта"""
        if self._active:
            self._active = False
        else:
            self._active = True

    async def join_to_chat(self, chat: str | int):
        """Метод добавления в чат. Возвращаем объект чата"""
        chat_info = await self._client.join_chat(chat_id=chat)
        chat = chat if 'https://t.me/' in chat else 'https://t.me/' + chat
        self._chat_dict[chat] = chat_info.id

# ========== Методы манипуляций информацией ==========
    def chats_dict_clean(self):
        """Очищаем словарь с чатами"""
        self._chat_dict = {}

    async def add_chat_info(self, chat):
        """Это метод, на случай, если в список добавляемых чатов, попал чат, в котором юзер бот уже состоит.
        В таком случае просто добавим необходимую информацию в словарь с чатами"""
        chat_info = await self._client.get_chat(chat_id=chat)
        chat = chat if 'https://t.me/' in chat else 'https://t.me/' + chat
        self._chat_dict[chat] = chat_info.id
        print(self._chat_dict)

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
                       f'<b>Мут:</b> <i>пока так</i>\n'
                       f'<b>На сколько чатов рассылает:</b> <i>пока так</i>')
        return info_string


test_account = Account(name='MyRevan', api_id=22761163,
                       api_hash='8b23c6b5877145fc046a0752a7cd20ac', phone_number='+375445337145')

account_dict['MyRevan'] = test_account

# test_account._client.start()

