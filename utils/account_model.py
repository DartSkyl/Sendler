from pyrogram import Client


account_list = list()


class Account:
    def __init__(self, name: str, api_id: int, api_hash: str, phone_number: str):
        self._name = name
        self._api_id = api_id
        self._api_hash = api_hash
        self._phone_number = phone_number
        self._client = Client(name=f'{name}', api_id=api_id, api_hash=api_hash, phone_number=phone_number)
        self._active = False

    async def start_session(self):
        """Здесь происходит авторизация аккаунта. Запрашиваем код и возвращаем хэш кода"""
        await self._client.connect()
        code_info = await self._client.send_code(self._phone_number)
        return code_info.phone_code_hash

    async def authorization_and_run(self, code_hash: str, code: str):
        """Здесь заканчиваем авторизацию и запускаемся"""
        await self._client.sign_in(phone_number=self._phone_number, phone_code_hash=code_hash, phone_code=code)
        await self._client.disconnect()
        await self._client.start()
        await self._client.send_message('DarthSkyl', 'Worked!')

    def get_active(self):
        """Возвращает статус аккаунта"""
        return self._active
