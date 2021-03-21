from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
from bot.db.repository import Repo


class DbMiddleware(LifetimeControllerMiddleware):
    def __init__(self, pool):
        super().__init__()
        self.pool = pool

    async def pre_process(self, obj, data, *args):
        con = await self.pool.acquire() # not recommended!!!
        data["conn"] = con
        data["repo"] = Repo(con)

    async def post_process(self, obj, data, *args):
        conn = data.get("conn")
        await self.pool.release(conn)
