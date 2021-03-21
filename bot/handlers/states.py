from aiogram.dispatcher.filters.state import StatesGroup, State


class UserStatus(StatesGroup):
    # Любой юзер пребывает в одном из 2-х состояний:
    waiting_code = State()
    access_true = State()

    waiting_address = State()
    waiting_payment = State()

    # Админ добавляет товар
    waiting_name = State()
    waiting_price = State()
    waiting_description = State()
    waiting_img_link = State()
