import asyncio
from datetime import datetime, timedelta
from typing import Coroutine


class Loop:
    def __init__(
        self,
        func: Coroutine,
        *,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        sleep_interval: int = 3
    ):
        self.func = func
        self._next_run = datetime.now()
        self._td_kwargs = {"hours": hours, "minutes": minutes, "seconds": seconds}
        self.sleep_interval = sleep_interval

    async def start(self, *args):
        while True:
            if datetime.now() > self._next_run:
                self._next_run += timedelta(**self._td_kwargs)
                await self.func(*args)

            await asyncio.sleep(self.sleep_interval)
