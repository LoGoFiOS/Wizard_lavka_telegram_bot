from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import IDFilter, Text

from bot import config
from bot.db.repository import Repo
from bot.handlers.states import UserStatus
from bot.utils.photo_link import photo_link_aiograph


async def cancel_add_item(m: types.Message):
    await m.answer("Никто никогда не узнает, что ты хотел выставить на витирну...")
    await UserStatus.access_true.set()


async def add_item(m: types.Message):
    await m.answer("Итак, как мы <b>это</b> будем называть?")
    await m.answer("Да, если передумаешь, просто скажи <b>отбой</b>")
    await UserStatus.waiting_name.set()


async def add_name(m: types.Message, state: FSMContext):
    await state.update_data(name=m.text)
    await m.answer("А сколько монет мы попросим за <b>эту</b>... вещь?")
    await UserStatus.waiting_price.set()


async def add_price(m: types.Message, state: FSMContext):
    await state.update_data(price=int(m.text))
    await m.answer("Дай описание для дорогих нашему сердцу покупателей:")
    await UserStatus.waiting_description.set()


async def add_description(m: types.Message, state: FSMContext):
    await state.update_data(description=m.text)
    await m.answer("Осталось предоставить картинку для каталога:")
    await UserStatus.waiting_img_link.set()


async def add_img_link(m: types.Message, state: FSMContext, repo: Repo):
    photo = m.photo[-1]
    await m.bot.send_chat_action(m.chat.id, 'upload_photo')
    img_link = await photo_link_aiograph(photo)
    await m.answer("Фото загрузилось")
    item_data = await state.get_data()
    await repo.add_item(name=item_data['name'], price=item_data['price'], description=item_data['description'],
                        img_link=img_link)

    await m.answer("Каталог пополнился!")
    await UserStatus.access_true.set()


def register_admin(dp: Dispatcher):
    dp.register_message_handler(cancel_add_item, IDFilter(user_id=config.admins),
                                Text(equals="отбой", ignore_case=True), state="*")
    dp.register_message_handler(add_item, IDFilter(user_id=config.admins), commands=["add"], state="*")
    dp.register_message_handler(add_name, IDFilter(user_id=config.admins), state=UserStatus.waiting_name)
    dp.register_message_handler(add_price, IDFilter(user_id=config.admins), state=UserStatus.waiting_price)
    dp.register_message_handler(add_description, IDFilter(user_id=config.admins), state=UserStatus.waiting_description)
    dp.register_message_handler(add_img_link, IDFilter(user_id=config.admins), content_types=types.ContentTypes.PHOTO,
                                state=UserStatus.waiting_img_link)
