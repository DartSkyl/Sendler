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

    async def join_to_chat(self, chat: str | int):
        """Метод добавления в чат. Возвращаем объект чата"""
        chat_info = await self._client.join_chat(chat_id=chat)
        self._chat_dict[chat_info.title] = chat_info.id

    def set_message_for_mailing(self, message: dict):
        """Передаем сюда словарь с сообщением и вливаем его в основной"""
        self._msg_dict.update(message)

    def get_messages_dict(self):
        """Возвращает словарь сообщений для рассылки"""
        return self._msg_dict

    def get_active(self):
        """Возвращает статус аккаунта"""
        return self._active

    def get_chats_dict(self):
        """Возвращает словарь с чатами в которых состоит юзер бот"""
        return self._chat_dict

    def change_activity(self):
        """Метод меняет состояние активности аккаунта"""
        if self._active:
            self._active = False
        else:
            self._active = True

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



