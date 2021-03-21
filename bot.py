import asyncio
import logging

import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.types import BotCommand
from aiograph import Telegraph

from bot import config
from bot.handlers.admin import register_admin
from bot.handlers.cart import register_cart
from bot.handlers.inline_mode import register_inline_mode
from bot.handlers.user import register_user
from bot.middlewares.postgres_middleware import DbMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.utils.photo_link import TelegraphClass

logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/me", description="Мой профиль"),
        BotCommand(command="/cart", description="Корзина покупок"),
        BotCommand(command="/shop", description="Каталог товаров"),
        BotCommand(command="/about", description="О боте")
    ]
    await bot.set_my_commands(commands)


async def create_tables(pool):
    await pool.execute(
        "CREATE TABLE IF NOT EXISTS Users ("
        "id INT NOT NULL, "
        "balance INT NOT NULL, "
        "ref_code varchar(255) NOT NULL, "
        "id_who_invited INT NOT NULL, "
        "ref_code_amount INT NOT NULL, "
        "PRIMARY KEY (id)"
        ");"
        "INSERT INTO Users (id, balance, ref_code, id_who_invited, ref_code_amount) "
        "VALUES(-1, 100, 'MrKakurasu', -10, 9999) ON CONFLICT DO NOTHING;"
        "CREATE TABLE IF NOT EXISTS Items ("
        "id SERIAL, "
        "name varchar(255) NOT NULL, "
        "price INT NOT NULL, "
        "description varchar(255) NOT NULL, "
        "img_link varchar(255) NOT NULL, "
        "PRIMARY KEY (id)"
        ");"
        "CREATE TABLE IF NOT EXISTS Bills ("
        "id SERIAL, "
        "billid varchar(255) NOT NULL, "
        "status varchar(255) NOT NULL, "
        "PRIMARY KEY (id)"
        ");"
    )


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=config.TELEGRAM_API_TOKEN, parse_mode=types.ParseMode.HTML)
    dp = Dispatcher(bot, storage=RedisStorage2(host=config.REDIS_HOST))

    # Работа с БД
    pool = await asyncpg.create_pool(
        user=config.PG_USER,
        password=config.PG_PASSWORD,
        host=config.PG_HOST,
        database=config.PG_DATABASE,
        command_timeout=60,
    )
    await create_tables(pool)

    telegraph = Telegraph()
    TelegraphClass.t = telegraph

    await set_commands(bot)

    dp.middleware.setup(DbMiddleware(pool))
    dp.middleware.setup(ThrottlingMiddleware())
    register_inline_mode(dp)
    register_admin(dp)
    register_user(dp)
    register_cart(dp)

    try:
        await dp.start_polling()
    finally:
        await bot.close()


if __name__ == '__main__':
    asyncio.run(main())

    # Работа с SQlite
    # import bot.db_docker.sqlite as database
    # db_docker = database.set_config(path_to_db='bot/db_docker/mysqlite.db_docker')

# TODO Оформить бота в Т
# TODO Репозиторий + описание + сайт
# TODO Тесты
# Если активный участник выдаст товар в инлайн моде, то сможет ли его купить неактивный?
# TODO id Latand


# TODO Добавить комментарии в коде
# TODO aiohttp
# TODO delete for adm
