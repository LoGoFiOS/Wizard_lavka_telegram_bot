from datetime import datetime

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils.callback_data import CallbackData

from bot.db.repository import Repo
from bot.handlers.states import UserStatus
from bot.utils import qiwi

cb_items = CallbackData("items", "id", "action")


async def add_item_to_cart(call: types.CallbackQuery, state: FSMContext):
    item_id = call.data.split("_")[2]
    user_data = await state.get_data()
    user_cart = user_data.get('cart')
    cart_msg_id = user_data.get('cart_msg_id')
    item_amount = user_cart.get(item_id)
    # await call.message.delete()
    if cart_msg_id:
        await call.bot.delete_message(call.message.chat.id, cart_msg_id)
        await state.update_data(cart_msg_id=None)
    if item_amount:
        user_cart[item_id] += 1
    else:
        user_cart[item_id] = 1
    await state.update_data(cart=user_cart)
    await call.bot.send_message(call.from_user.id, 'Добавлено! Посмотреть корзину и изменить количество: /cart')
    await call.answer(cache_time=5)


async def show_cart(m: types.Message, repo: Repo, state: FSMContext):
    user_data = await state.get_data()
    user_cart = user_data.get('cart')
    cart_msg_id = user_data.get('cart_msg_id')
    if not user_cart:
        return
    if cart_msg_id:
        await m.bot.delete_message(m.chat.id, cart_msg_id)
        await state.update_data(cart_msg_id=None)
    msg = await m.answer(await get_cart_msg(m.from_user.id, repo, state),
                         reply_markup=await get_cart_keyboard(user_cart))
    await state.update_data(cart_msg_id=msg.message_id)


async def cart_clear(call: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    user_cart = user_data.get('cart').clear()
    await state.update_data(cart=dict())
    cart_msg_id = user_data.get('cart_msg_id')
    await call.bot.edit_message_text(text=f"Корзина очищена!", chat_id=call.message.chat.id,
                                     message_id=cart_msg_id,
                                     reply_markup=await get_cart_keyboard(user_cart))
    await call.answer()


async def cart_buy(call: types.CallbackQuery):
    await call.message.delete()
    await UserStatus.waiting_address.set()
    await call.bot.send_message(call.from_user.id,
                                'Оформляем заказ. Итак, куда доставляем-с? Для отмены заказа просто скажите: <b>отмена</b>')
    await call.answer()


async def cart_cancel(call: types.CallbackQuery):
    # можно не удалять, всё равно перезапишутя в get_cart_msg() и add_address()
    # del user_data['must_pay']
    # del user_data['balance']
    # del user_data['address']
    await UserStatus.access_true.set()
    await call.answer()


async def add_address(m: types.Message, repo: Repo, state: FSMContext):
    user_data = await state.get_data()
    must_pay = user_data['must_pay']
    balance = user_data['balance']
    await repo.change_balance(m.from_user.id, balance)

    await state.update_data(address=m.text)
    await UserStatus.waiting_payment.set()

    # формирование укникального номера выставляемого счёта и занесение его в БД
    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y_%H_%M_%S")
    billid = f"{m.from_user.id}_{dt_string}"
    await repo.add_bill(billid)
    await state.update_data(billid=billid)

    keyboard_markup = types.InlineKeyboardMarkup()
    keyboard_markup.add(types.InlineKeyboardButton(text='Оплатил', callback_data="pay_check"))
    link = str(qiwi.get_invoice(str(billid), float(must_pay)))
    txt = f"Адрес сохранён." \
          f"Оплатите заказ на сумму {must_pay} 💎 по ссылке ниже и нажмите после этого на кнопку: <b>Оплатил</b>\n\n" \
          f"{link}"
    await m.answer(txt, reply_markup=keyboard_markup)


async def check_payment(call: types.CallbackQuery, repo: Repo, state: FSMContext):
    user_data = await state.get_data()
    billid = user_data['billid']

    if qiwi.is_bill_paid(billid):
        await call.message.answer("Отлично! Ждите посылку от DragonFlyExpress!")
        # Так статус не присваивается!
        # UserStatus.access_true.set()
        await repo.update_bill_paid(billid)
        await state.set_state(UserStatus.access_true)
        await call.message.delete()
    else:
        await call.message.answer("Счёт не оплачен! Попробуйте ещё раз...")
    await call.answer()


async def cart_item_plus(call: types.CallbackQuery, callback_data: dict, repo: Repo, state: FSMContext):
    item_id = callback_data["id"]
    user_data = await state.get_data()
    user_cart = user_data.get('cart')
    cart_msg_id = user_data.get('cart_msg_id')
    user_cart[item_id] += 1
    await state.update_data(cart=user_cart)
    await call.bot.edit_message_text(text=await get_cart_msg(call.from_user.id, repo, state),
                                     chat_id=call.message.chat.id,
                                     message_id=cart_msg_id,
                                     reply_markup=await get_cart_keyboard(user_cart))
    await call.answer()


async def cart_item_minus(call: types.CallbackQuery, callback_data: dict, repo: Repo, state: FSMContext):
    item_id = callback_data["id"]
    user_data = await state.get_data()
    user_cart = user_data.get('cart')
    cart_msg_id = user_data.get('cart_msg_id')
    user_cart[item_id] -= 1
    if user_cart[item_id] == 0:
        del user_cart[item_id]
    await state.update_data(cart=user_cart)
    await call.bot.edit_message_text(text=await get_cart_msg(call.from_user.id, repo, state),
                                     chat_id=call.message.chat.id,
                                     message_id=cart_msg_id,
                                     reply_markup=await get_cart_keyboard(user_cart))
    await call.answer()


def register_cart(dp: Dispatcher):
    dp.register_callback_query_handler(add_item_to_cart, Text(startswith="add_item_"), state=UserStatus.access_true)
    dp.register_message_handler(show_cart, commands=["cart"], state=UserStatus.access_true)
    dp.register_callback_query_handler(cart_clear, Text(equals="cart_clear"), state="*")
    dp.register_callback_query_handler(cart_buy, Text(equals="cart_buy"), state="*")
    dp.register_message_handler(cart_cancel, Text(equals="отмена", ignore_case=True), state=UserStatus.waiting_address)
    dp.register_message_handler(add_address, state=UserStatus.waiting_address)
    dp.register_callback_query_handler(check_payment, Text(equals="pay_check"), state="*")
    dp.register_callback_query_handler(cart_item_plus, cb_items.filter(action="cart_plus"), state="*")
    dp.register_callback_query_handler(cart_item_minus, cb_items.filter(action="cart_minus"), state="*")


async def get_cart_keyboard(user_cart: dict):
    if not user_cart:
        return None
    keyboard_markup = types.InlineKeyboardMarkup()
    keyboard_markup.add(types.InlineKeyboardButton(text='Оформить', callback_data="cart_buy"),
                        types.InlineKeyboardButton(text='Каталог', switch_inline_query_current_chat=""))

    for i in user_cart:
        b = (
            types.InlineKeyboardButton(text='-', callback_data=cb_items.new(id=i, action='cart_minus')),
            types.InlineKeyboardButton(text=f"{user_cart[i]} шт.", callback_data="data"),
            types.InlineKeyboardButton(text='+', callback_data=cb_items.new(id=i, action='cart_plus')),
        )
        keyboard_markup.add(*b)
    keyboard_markup.add(
        types.InlineKeyboardButton(text='Очистить', callback_data='cart_clear'))
    return keyboard_markup


async def get_cart_msg(user_id: int, repo: Repo, state: FSMContext) -> str:
    user_data = await state.get_data()
    user_cart = user_data.get('cart')
    cart_sum = 0
    user = await repo.get_user(id=user_id)
    user_balance = user['balance']
    result = f"Корзина: \n\n"
    for i in enumerate(user_cart):
        item_id = i[1]
        item = await repo.get_item(int(item_id))
        price = item['price'] * user_cart[item_id]
        cart_sum += price
        result += f"{i[0] + 1}. {item['name']}:\n" \
                  f"<code>{item['price']} 💎 x {user_cart[item_id]} шт. = {price} 💎</code>" \
                  f"\n\n"

    result += f"Всего: {cart_sum} 💎\n"
    result += f"Баланс кошелька: {user_balance} 💎\n\n"

    if cart_sum > user_balance:
        result += f"Списываем с кошелька: {user_balance} 💎\n"
        result += f"Остаётся в кошельке: 0 💎\n"
        result += f"Итого: {cart_sum - user_balance} 💎"
        await state.update_data(must_pay=cart_sum - user_balance, balance=0)
    else:
        result += f"Списываем с кошелька: {cart_sum - 1} 💎\n"
        result += f"Остаётся в кошельке: {user_balance - cart_sum - 1} 💎\n"
        result += f"Итого: 1 💎"
        await state.update_data(must_pay=1, balance=user_balance - cart_sum - 1)

    return result
