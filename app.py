import asyncio
import datetime
import handlers  # noqa
from loader import dp, bot
from utils.account_model import test_account


async def start_up():
    # with open('bot.log', 'a') as log_file:
    #     log_file.write(f'\n========== New bot session {datetime.datetime.now()} ==========\n\n')
    await test_account._client.start()
    print('Стартуем')
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(start_up())
    except KeyboardInterrupt:
        print('Хорош, бро')
