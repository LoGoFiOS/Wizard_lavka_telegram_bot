# from aiogram.dispatcher.middlewares import BaseMiddleware
# from aioredis.pool import ConnectionsPool
# from aiogram import types
# from typing import Dict, Any
#
#
# class RedisMiddleware(BaseMiddleware):
#     def __init__(self, redis_storage: ConnectionsPool):
#         super(RedisMiddleware, self).__init__()
#         self.redis = redis_storage
#
#     async def on_pre_process_message(self, message: types.Message, data: Dict[str, Any]):
#         data["redis"] = self.redis

    # async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: Dict[str, Any]):
    #     data["redis"] = self.redis
