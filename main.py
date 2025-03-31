import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS", "").split(",")))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

from aiogram import types
import subprocess


async def get_short_service_status(service_name="reels_bot.service") -> str:
    """Возвращает текущий статус сервиса"""

    result = subprocess.run(
        ["systemctl", "is-active", service_name],
        capture_output=True,
        text=True
    )
    status = result.stdout.strip()
    return "🟢 Активен" if status == "active" else "🔴 Неактивен"


async def create_status_keyboard():
    """Создает клавиатуру с текущим статусом"""
    status = await get_short_service_status()
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Статус: {status}", callback_data="show_status")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_status")]
    ])


@dp.callback_query(lambda c: c.data == "refresh_status")
async def refresh_status(callback: types.CallbackQuery):
    try:
        # Получаем новую клавиатуру
        new_kb = await create_status_keyboard()

        # Получаем текущий текст кнопки статуса
        current_status = callback.message.reply_markup.inline_keyboard[0][0].text
        new_status = new_kb.inline_keyboard[0][0].text

        # Обновляем только если статус изменился
        if current_status != new_status:
            await callback.message.edit_reply_markup(reply_markup=new_kb)
            await callback.answer("Статус обновлён!")
        else:
            await callback.answer("Статус не изменился")

    except TelegramBadRequest:
        await callback.answer("Статус не изменился")


@dp.callback_query(lambda c: c.data == "show_status")
async def show_status(callback: types.CallbackQuery):
    status = await get_short_service_status()
    await callback.answer(f"Текущий статус: {status}", show_alert=True)


@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    kb = await create_status_keyboard()
    await message.answer("Статус сервиса:", reply_markup=kb)


main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Узнать IP")],
        [KeyboardButton(text="Статус сервиса")]
    ],
    resize_keyboard=True,
    selective=False
)


def aus_ip_getter():
    result = subprocess.run(["wget", "-qO-", "eth0.me"], stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def get_service_status(service_name="reels_bot.service"):
    """Получает статус systemd сервиса"""

    # Сначала проверяем общее состояние (active/inactive)
    is_active = subprocess.run(
        ["systemctl", "is-active", service_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    ).stdout.strip() == "active"

    # Получаем полный статус
    status_result = subprocess.run(
        ["systemctl", "status", service_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )

    # Фильтруем нужные строки
    output_lines = []
    for line in status_result.stdout.splitlines():
        line = line.strip()
        if line.startswith(('Loaded:', 'Active:')):
            output_lines.append(line)

    # Добавляем индикатор
    status_icon = "🟢" if is_active else "🔴"
    if output_lines:
        output_lines[0] = f"{status_icon} {output_lines[0]}"

    return '\n'.join(output_lines) if output_lines else f"{status_icon} Service status not available"


@dp.message(Command('start'))
async def start(message: Message):
    if message.chat.id in ALLOWED_USERS:
        await message.answer(f'Привет, {message.from_user.first_name}!', reply_markup=main_kb)


@dp.message(F.text == 'Узнать IP')
async def ip_sender(message: Message):
    if message.chat.id in ALLOWED_USERS:
        await message.answer(f'Текущий ip-адрес сервера:: {aus_ip_getter()}')


@dp.message(F.text == 'Статус сервиса')
async def ip_sender(message: Message):
    if message.chat.id in ALLOWED_USERS:
        await message.answer(f'{get_service_status()}')


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
