import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS", "").split(",")))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

from aiogram import types
import subprocess

# Конфигурация сервисов (легко добавлять новые)
SERVICES = {
    "reels_bot": "reels_bot.service",
    "openvpn": "openvpn.service",
    "apache": "apache2.service"
}


async def get_short_service_status(service_name: str) -> str:
    """Возвращает статус сервиса с иконкой"""

    result = subprocess.run(
        ["systemctl", "is-active", service_name],
        capture_output=True, text=True, timeout=3
    )
    status = result.stdout.strip()
    return "🟢" if status == "active" else "🔴"


async def create_services_keyboard() -> types.InlineKeyboardMarkup:
    """Генерирует клавиатуру с актуальными статусами"""
    buttons = []

    # Собираем статусы асинхронно
    for service_key, service_name in SERVICES.items():
        status_icon = await get_short_service_status(service_name)
        buttons.append([
            types.InlineKeyboardButton(
                text=f"{status_icon} {service_key}",
                callback_data=f"service_detail:{service_key}"
            )
        ])

    # Добавляем кнопку обновления
    buttons.append([
        types.InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data="refresh_services"
        )
    ])

    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.callback_query(F.data == "refresh_services")
async def refresh_services_handler(callback: types.CallbackQuery):
    """Обработчик обновления статусов"""

    new_kb = await create_services_keyboard()

    # Сравниваем с текущей клавиатурой
    current_kb = callback.message.reply_markup.inline_keyboard
    new_kb_data = new_kb.inline_keyboard

    # Проверяем изменения в статусах
    has_changes = any(
        current_btn.text != new_btn.text
        for current_row, new_row in zip(current_kb, new_kb_data)
        for current_btn, new_btn in zip(current_row, new_row)
    )

    if has_changes:
        await callback.message.edit_reply_markup(reply_markup=new_kb)
        await callback.answer("Статусы обновлены!")
    else:
        await callback.answer("Статусы не изменились")


@dp.callback_query(F.data.startswith("service_detail:"))
async def service_detail_handler(callback: types.CallbackQuery):
    """Показывает детали сервиса"""
    service_key = callback.data.split(":")[1]
    service_name = SERVICES[service_key]

    try:
        # Получаем подробный статус
        result = subprocess.run(
            ["systemctl", "status", service_name],
            capture_output=True, text=True, timeout=5
        )
        status_text = result.stdout.split('\n')[0:3]  # Берем первые 3 строки
        await callback.answer(
            "\n".join(status_text),
            show_alert=True
        )
    except Exception as e:

        await callback.answer(f"Ошибка получения статуса: {e}", show_alert=True)


@dp.message(F.text == "Статус сервисов")
async def status_command(message: types.Message):
    """Обработчик команды /status"""
    kb = await create_services_keyboard()
    await message.answer(
        "📊 Статус сервисов:",
        reply_markup=kb
    )


main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Узнать IP")],
        [KeyboardButton(text="Статус сервисов")]
    ],
    resize_keyboard=True,
    selective=False
)


def aus_ip_getter():
    result = subprocess.run(["wget", "-qO-", "eth0.me"], stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


@dp.message(Command('start'))
async def start(message: Message):
    if message.chat.id in ALLOWED_USERS:
        await message.answer(f'Привет, {message.from_user.first_name}!', reply_markup=main_kb)


@dp.message(F.text == 'Узнать IP')
async def ip_sender(message: Message):
    if message.chat.id in ALLOWED_USERS:
        await message.answer(f'Текущий ip-адрес сервера:: {aus_ip_getter()}')


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
