import asyncio
import re

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.filters import Text
from aiogram.utils.markdown import hide_link

from bot import config
from bot.db.repository import Repo
from bot.handlers.states import UserStatus
from bot.utils.ref_generator import get_ref


async def show_about(m: types.Message):
    txt = "Волшебная Лавка Чудесного и Невероятного\n" \
          "Это финальное задание курса от @Latand.\n" \
          "https://www.udemy.com/course/aiogram-python/\n\n" \
          "Исходный код открыт:\n" \
          "https://github.com/LoGoFiOS/Wizard_lavka_telegram_bot\n\n" \
          "В репозитории вы сможете найти ТЗ на бота, инструкцию по запуску, а так же доп. информацию, " \
          "которая может быть полезна.\n" \
          "Если есть замечания/предложения — пишите @LoGoFiOS"
    await m.answer(txt)


async def set_state(m: types.Message, state: FSMContext):
    """
    Возможность перейти в статус ожидания ввода реферального кода. На вскяий случай.
    """
    await m.answer("State = waiting_code")
    await UserStatus.waiting_code.set()
    await state.update_data({'cart': {}, 'cart_msg_id': None})


async def show_shop(m: types.Message):
    """
    Выдаёт сообщение, в котором кнопка, открывающая каталог.
    Сообщение удалется через 3 сек.
    """
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Каталог', switch_inline_query_current_chat=""))
    msg = await m.answer("Нажми, чтобы посмотреть:", reply_markup=keyboard)
    await asyncio.sleep(3.0)
    await msg.delete()


async def user_info(m: types.Message, repo: Repo):
    """
    Выдаёт сообщение с информацией о профиле пользовтеля.
    """
    row = await repo.get_user(id=m.from_user.id)
    await m.answer(f"Кошель: {row['balance']} 💎\n"
                   f"Кстати, за каждого нового участника кошелёк потяжелеет на 10 💎!")
    txt = f"Пароль для приглашения новых участников: {row['ref_code']}\n" \
          f"Пригласительная ссылка: \n" \
          f"https://t.me/WizardLavka_bot?start=ref_{row['ref_code']}"
    await m.answer(txt)


async def secret_code(m: types.Message):
    """
    При регистрации (state == UserStatus.waiting_code) можно напистаь в чат "пожалуйста" и будет выдано сообщение
    с паролем. Если затем написать этот пароль, т.е. 'MrKakurasu', и пользователь будет зарегистрирован.
    Этот пароль создаётся при инициализации БД (см. bot.py).
    """
    await m.answer("Секретный пароль хозяина лавки: MrKakurasu")


async def start_item_id(m: types.Message, repo: Repo):
    """
    Обработка нажатия на кнопку "хочу купить", которая прикреплена к результату выдачи inline запроса.
    Про кнопку см. get_inline_answer_keyboard() в inline_mode.py

    Показывает товар. Если пользователь не зарегистрирован, то state = waiting_code
    """
    item_id = m.get_args()[5::]
    item = await repo.get_item(int(item_id))
    # Оставить проверку на случай махинаций с диплинками
    if not item:
        return
    await m.answer(await item_msg(item), parse_mode=types.ParseMode.HTML,
                   reply_markup=await get_item_keyboard(int(item_id), m.from_user.id))

    # Оставить проверку на случай махинаций с диплинками
    if await is_user_exist(m, repo):
        # await m.answer(f"Постойте-ка. Да ведь вы <i>уже</i> наш покупатель!")
        return
    await UserStatus.waiting_code.set()
    await m.answer(await hi_msg())


async def start_ref_link(m: types.Message, repo: Repo, state: FSMContext):
    """
    Обработка перехода пользователя по реферальной ссылке вида: https://t.me/WizardLavka_bot?start=ref_REFCODE

    Из ссылки достаётся вшитый реферальный код ref и проверяется на валидность.
    """
    if await is_user_exist(m, repo):
        await m.answer(f"Постойте-ка. Да ведь вы <i>уже</i> наш покупатель!")
        return
    ref = m.get_args()[4::]
    await m.answer(f"Вы пришли по реферальной ссылке с паролем: {ref}")
    if await is_code_valid(m, repo, ref):
        await add_user(m, ref, repo, state)
    else:
        await UserStatus.waiting_code.set()


async def reading_code(m: types.Message, repo: Repo, state: FSMContext):
    """
    Сообщение пользователя (state == waiting_code) - реферальный код. Проверяет его валидность.
    """
    if await is_code_valid(m, repo, m.text):
        await add_user(m, m.text, repo, state)


async def start_base(m: types.Message, repo: Repo):
    """
    Обработка /start.

    Пользователь переводится в состояние waiting_code, т.е. он должен либо ввести реферальный код сам,
    либо пройти по реферальной ссылке.
    """
    if await is_user_exist(m, repo):
        await m.answer(f"Постойте-ка. Да ведь вы <i>уже</i> наш покупатель!")
        return
    await UserStatus.waiting_code.set()
    await m.answer(await hi_msg())


def register_user(dp: Dispatcher):
    dp.register_message_handler(show_about, commands=["about"], state="*")
    dp.register_message_handler(set_state, commands=["set"], state="*")
    dp.register_message_handler(show_shop, commands=["shop"], state="*")
    dp.register_message_handler(user_info, commands=["me"], state=UserStatus.access_true)
    dp.register_message_handler(secret_code, Text(equals="пожалуйста", ignore_case=True),
                                state=UserStatus.waiting_code)
    dp.register_message_handler(start_item_id, CommandStart(deep_link=re.compile(r"item_([\w]+)")), state="*")
    dp.register_message_handler(start_ref_link, CommandStart(deep_link=re.compile(r"ref_([\w]+)")), state="*")
    dp.register_message_handler(reading_code, state=UserStatus.waiting_code)
    dp.register_message_handler(start_base, commands=["start"], state="*")


async def is_user_exist(m: types.Message, repo: Repo):
    """
    Существует ли пользователь в БД Postgres.
    """
    row = await repo.get_user(id=m.from_user.id)
    return row is not None


async def is_code_valid(m: types.Message, repo: Repo, ref: str):
    """
    Проверка валидности реферального кода. Т.е. зарегистрирован ли такой пользователь, у которого реферальный код == ref

    ref - реферальный код который пользователь ввёл сам или который был вшит в реферальную ссылку.
    """
    await m.answer("Листаем книгу тайн... Сверяем записи...")
    row = await repo.check_ref(ref)
    if row is None:
        await m.answer(
            f"Пароль {ref} неверен! "
            f"Введите пароль ещё раз или попросите ссылку-приглашение у любого действующего покупателя!")
        return False
    return True


async def add_user(m: types.Message, ref: str, repo: Repo, state: FSMContext):
    """
    Добавить пользователя в БД Postgres.

    ref - реферальный код который пользователь ввёл сам или который был вшит в реферальную ссылку по которой он прошёл.

    Каждый зарегистрированный пользователь имеет реферальный код, который может быть использован для регистрации
    нового пользователя. Генерация пароля см. bot/utils/ref_generator.py

    Тому пользователю, у которого реферальный код == ref, начиляются монеты на счёт.
    """
    id_who_invited = await repo.get_user(ref_code=ref)
    await repo.add_user(m.from_user.id, get_ref(m.from_user.id), id_who_invited["id"])
    await repo.add_coins_ref(id_who_invited=id_who_invited["id"])
    await state.update_data({'cart': {}, 'cart_msg_id': None})
    await m.answer("Добро пожаловать в Волшебную Лавку Чудесного и Невероятного!")
    await UserStatus.access_true.set()


async def hi_msg():
    return "\n\n".join(
        [
            "Доброго пожаловать в Лавку Чудесного и Невероятного - здесь можно найти самые удивительные вещи "
            "со всего света.",
            "Вход не для всех, вы же понимаете...",
            "Назовите секретный пароль, который можно спросить у любого активного покупателя.",
            "Впрочем, если вы скажите мне <b>волшебное слово</b>, то так и быть - я поделюсь своим.",
        ])


async def item_msg(item) -> str:
    """
    Формат вывода информации о товаре.
    """
    return f"<b>{item['name']}</b>\n\n" \
           f"{item['description']}\n\n" \
           f"Цена: {item['price']} 💎\n" \
           f"{hide_link(item['img_link'])}"


async def get_item_keyboard(item_id: int, user_id: int):
    """
    Клавиатура, которая крепится к сообщению с информацией о товаре.
    """
    if user_id in config.admins:
        return types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton('В корзину!', callback_data=f'add_item_{item_id}')
            ],
            # TODO: реализовать возможность удаления из БД предмета этой кнопкой
            [
                types.InlineKeyboardButton('Изъять из каталога!', callback_data=f'del_item_{item_id}')
            ],
        ])
    else:
        return types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton('В корзину!', callback_data=f'add_item_{item_id}')
            ],
        ])

# dp.register_message_handler(adm_unset, commands=["unset"], state="*")
# dp.register_message_handler(adm_clear, commands=["clear"], state="*")
# dp.register_message_handler(adm_coins, commands=["coins"], state="*")
# dp.register_callback_query_handler(show_item, Text(startswith="item_"), state="*")

# async def show_item(call: types.CallbackQuery, repo: Repo):
#     item_id = call.data.split("_")[1]
#     item = await repo.get_item(int(item_id))
#     await call.bot.send_message(call.from_user.id, await item_msg(item), parse_mode=types.ParseMode.HTML,
#                                 reply_markup=await get_item_keyboard(int(item_id), call.from_user.id))
#     await call.answer()


# async def adm_set(m: types.Message, repo: Repo, state: FSMContext):
#     await m.answer("State = accessTrue")
#     await UserStatus.access_true.set()
#     await state.update_data({'cart': {}, 'cart_msg_id': None})
#
#
# async def adm_unset(m: types.Message, repo: Repo, state: FSMContext):
#     await m.answer("State.finish()")
#     await state.finish()


# async def adm_clear(m: types.Message, repo: Repo, state: FSMContext):
#     await m.answer("State reset")
#     await state.finish()
#     await state.update_data({'cart': {}, 'cart_msg_id': None})
#     await UserStatus.access_true.set()
#
#
# async def adm_coins(m: types.Message, repo: Repo, state: FSMContext):
#     await m.answer("add coins")
#     await repo.change_balance(m.from_user.id, 10)


# async def adm_del(m: types.Message, repo: Repo, state: FSMContext):
#     await m.answer("del user")
#     await UserStatus.access_true.set()
