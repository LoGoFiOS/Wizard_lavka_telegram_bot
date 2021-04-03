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
            types.InlineKeyboardButton('Рассмотреть ближе...', callback_data=f'show_item_{item_id}')
        ],
    ])
