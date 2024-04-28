from datetime import datetime
from typing import Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler


class MailingCore:
    def __init__(self):
        self._scheduler = AsyncIOScheduler(gconfig={'apscheduler.timezone': 'Europe/Moscow'})
        self._scheduler.start()

    async def add_mailing_job(self, interval: int, mailing: Callable, user_bot_name: str):
        """Метод формирует работу по рассылке для планировщика"""
        self._scheduler.add_job(func=mailing, trigger='interval',
                                minutes=interval, next_run_time=datetime.now(),
                                id=user_bot_name, max_instances=1,
                                replace_existing=True)

    async def stop_mailing(self, user_bot_name: str):
        """Так мы остановим рассылку"""
        self._scheduler.remove_job(user_bot_name)

