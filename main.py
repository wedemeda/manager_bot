import asyncio
import logging
import os
import subprocess

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS", "").split(",")))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


def aus_ip_getter():
    result = subprocess.run(["wget", "-qO-", "eth0.me"], stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


@dp.message(Command('start'))
async def start(message: Message):
    if message.chat.id in ALLOWED_USERS:
        await message.answer(f'Привет, {message.from_user.first_name}!')


@dp.message(F.text == 'Узнать текущий ip сервера')
async def ip_sender(message: Message):
    if message.chat.id in ALLOWED_USERS:
        await message.answer(f'Текущий ip-адрес сервера:: {aus_ip_getter()}')


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
