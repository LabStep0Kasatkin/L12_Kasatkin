from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import requests

from config import BOT_TOKEN, WEATHER_API_KEY, ADMIN_ID
from database import init_db, add_or_update_user

from mykeyboard import get_main_keyboard, gender_kb, get_hour_kb, get_minute_kb, get_weather_smile
from utils import show_users_handler

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Registration(StatesGroup):
    gender = State()
    notification_hour = State()
    notification_minute = State()
    notification_freq = State()


@dp.message(CommandStart())
async def start(message: Message):
    is_admin = message.from_user.id == int(ADMIN_ID)
    await message.answer("Привет! Я бот для определения погоды.", reply_markup=get_main_keyboard(is_admin))


@dp.message(F.text == "Пользователи")
async def show_users(message: Message):
    await show_users_handler(message, ADMIN_ID)


@dp.message(F.text == "Узнать погоду")
async def get_weather(message: Message):
    url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q=Moscow"

    response = requests.get(url)
    data = response.json()

    if "error" in data:
        await message.answer("Ошибка получения погоды.")
        return

    temp_c = data["current"]["temp_c"]
    emoji = get_weather_smile(temp_c)
    await message.answer(f"{emoji} Температура в Москве: {temp_c}°C")


@dp.message(F.text == "Регистрация")
async def registration_start(message: Message, state: FSMContext):
    await state.set_state(Registration.gender)
    await message.answer("Выберите ваш пол:", reply_markup=gender_kb)


@dp.message(Registration.gender)
async def registration_gender(message: Message, state: FSMContext):
    gender = message.text
    if gender not in ["Мужской", "Женский"]:
        await message.answer("Пожалуйста, выберите пол с помощью кнопок.")
        return
    await state.update_data(gender=gender)
    await state.set_state(Registration.notification_hour)
    await message.answer("Выберите час уведомления:", reply_markup=get_hour_kb())


@dp.message(Registration.notification_hour)
async def registration_hour(message: Message, state: FSMContext):
    hour = message.text
    if not hour.isdigit() or not (0 <= int(hour) <= 23):
        await message.answer("Пожалуйста, выберите час с помощью кнопок.")
        return
    await state.update_data(notification_hour=hour)
    await state.set_state(Registration.notification_minute)
    await message.answer("Выберите минуты уведомления:", reply_markup=get_minute_kb())


@dp.message(Registration.notification_minute)
async def registration_minute(message: Message, state: FSMContext):
    minute = message.text
    if not minute.isdigit() or not (0 <= int(minute) <= 59) or int(minute) % 5 != 0:
        await message.answer("Пожалуйста, выберите минуты с помощью кнопок.")
        return
    await state.update_data(notification_minute=minute)
    await state.set_state(Registration.notification_freq)
    await message.answer("Введите частоту уведомлений (например, ежедневно или еженедельно):", reply_markup=ReplyKeyboardRemove())


@dp.message(Registration.notification_freq)
async def registration_notification_freq(message: Message, state: FSMContext):
    freq = message.text
    data = await state.get_data()
    user_data = {
        "telegram_id": message.from_user.id,
        "username": message.from_user.username,
        "gender": data["gender"],
        "notification_time": f"{data['notification_hour']}:{data['notification_minute']}",
        "notification_freq": freq
    }
    await add_or_update_user(**user_data)
    await message.answer("Вы успешно зарегистрированы!", reply_markup=get_main_keyboard(message.from_user.id == int(ADMIN_ID)))
    await state.clear()


async def main():
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())