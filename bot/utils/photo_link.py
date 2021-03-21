from dataclasses import dataclass
from io import BytesIO

from aiogram import types
from aiograph import Telegraph


@dataclass
class TelegraphClass:
    t: Telegraph


async def photo_link_aiograph(photo: types.photo_size.PhotoSize) -> str:
    with await photo.download(BytesIO()) as file:
        links = await TelegraphClass.t.upload(file)
    return links[0]
