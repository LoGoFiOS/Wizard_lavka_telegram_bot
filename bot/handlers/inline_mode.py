from aiogram import Dispatcher, types
from aiogram.dispatcher.filters import Text

from bot.db.repository import Repo


async def show_all_items_query(query: types.InlineQuery, repo: Repo):
    items = await repo.show_all_items()
    articles = [types.InlineQueryResultArticle(
        id=item['id'],
        title=item['name'],
        description=item['description'],
        thumb_url=item['img_link'],
        input_message_content=types.InputTextMessageContent(
            message_text=f"<b>{item['name']}</b>\n\n"
                         f"{item['description']}\n\n"
                         f"⬇ Подробнее ⬇",
            parse_mode="HTML",
        ),
        reply_markup=await get_inline_keyboard(item['id'])
    ) for item in items]

    await query.answer(articles, cache_time=2, is_personal=True)


async def show_items_query(query: types.InlineQuery, repo: Repo):
    if len(query.query) > 2:
        items = await repo.get_items(query.query)
        articles = [types.InlineQueryResultArticle(
            id=item['id'],
            title=item['name'],
            description=item['description'],
            thumb_url=item['img_link'],
            input_message_content=types.InputTextMessageContent(
                message_text=f"<b>{item['name']}</b>\n\n"
                             f"{item['description']}\n\n"
                             f"⬇ Подробнее ⬇",
                parse_mode="HTML",
            ),
            reply_markup=await get_inline_keyboard(item['id'])
        ) for item in items]
        await query.answer(articles, cache_time=2, is_personal=True)


def register_inline_mode(dp: Dispatcher):
    dp.register_inline_handler(show_all_items_query, Text(equals=""), state="*")
    dp.register_inline_handler(show_items_query, state="*")


async def get_inline_keyboard(item_id: int):
    """
    Клавиатура, которая крепится к товару, выдаваемого в inline режиме.
    """
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton('Хочу купить!',
                                       url=f"https://t.me/WizardLavka_bot?start=item_{item_id}")
        ],
    ])

# async def get_inline_keyboard_bot_chat(item_id: int):
#     """
#     Клавиатура, которая крепится к товару, выдаваемого в inline режиме. Для запросов В ЧАТЕ С БОТОМ.
#     """
#     # if await state.get_state() == UserStatus.access_true.state:
#     return types.InlineKeyboardMarkup(inline_keyboard=[
#         [
#             types.InlineKeyboardButton('Рассмотреть поближе...', callback_data=f'item_{item_id}')
#         ],
#     ])

# async def show_item(call: types.CallbackQuery, repo: Repo):
#     item_id = call.data.split("_")[1]
#     item = await repo.get_item(int(item_id))
#     await call.bot.send_message(call.from_user.id, await item_msg(item), parse_mode=types.ParseMode.HTML,
#                                 reply_markup=await get_item_keyboard(int(item_id), call.from_user.id))
#     await call.answer()


# async def get_item_keyboard(item_id: int, user_id: int):
#     if user_id in config.admins:
#         return types.InlineKeyboardMarkup(inline_keyboard=[
#             [
#                 types.InlineKeyboardButton('В корзину!', callback_data=f'add_item_{item_id}')
#             ],
#             [
#                 types.InlineKeyboardButton('Изъять из каталога!', callback_data=f'del_item_{item_id}')
#             ],
#         ])
#     else:
#         return types.InlineKeyboardMarkup(inline_keyboard=[
#             [
#                 types.InlineKeyboardButton('В корзину!', callback_data=f'add_item_{item_id}')
#             ],
#         ])


# async def item_msg(item) -> str:
#     return f"<b>{item['name']}</b>\n\n" \
#            f"{item['description']}\n\n" \
#            f"Цена: {item['price']} 💎\n" \
#            f"{hide_link(item['img_link'])}"
