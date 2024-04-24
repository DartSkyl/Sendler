import asyncio
import datetime
import handlers  # noqa
from loader import dp, bot


async def start_up():
    with open('bot.log', 'a') as log_file:
        log_file.write(f'\n========== New bot session {datetime.datetime.now()} ==========\n\n')
    print('Стартуем')
    await dp.start_polling(bot,
                           allowed_updates=[
                               "message",
                               "callback_query",
                               "pre_checkout_query",
                               "chat_member"
                           ])


if __name__ == '__main__':
    try:
        asyncio.run(start_up())
    except KeyboardInterrupt:
        print('Хорош, бро')
