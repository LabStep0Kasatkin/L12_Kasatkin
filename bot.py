# bot.py
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import requests
from config import BOT_TOKEN, WEATHER_API_KEY
from database import get_users, init_db, add_or_update_user, get_user
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import ADMIN_ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Registration(StatesGroup):
    gender = State()
    notification_hour = State()
    notification_minute = State()
    notification_freq = State()

# Клавиатура
def get_main_keyboard(is_admin=False):
    buttons = [
        [KeyboardButton(text="Узнать погоду")],
        [KeyboardButton(text="Регистрация")]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="Пользователи")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Клавиатура для выбора пола
gender_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Функция для создания клавиатуры с часами (0-23)
def get_hour_kb():
    buttons = []
    row = []
    for h in range(0, 24):
        row.append(KeyboardButton(text=str(h)))
        if len(row) == 6:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

# Функция для создания клавиатуры с минутами (0-59, шаг 5)
def get_minute_kb():
    buttons = []
    row = []
    for m in range(0, 60, 5):
        row.append(KeyboardButton(text=str(m)))
        if len(row) == 6:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)


def get_weather_smile(temp_c):
    if temp_c < 0:
        return "❄️"
    elif 0 <= temp_c < 15:
        return "🧥"
    elif 15 <= temp_c < 25:
        return "🌤️"
    else:
        return "🔥"

@dp.message(CommandStart())
async def start(message: Message):
    is_admin = message.from_user.id == int(ADMIN_ID)
    await message.answer("Привет! Я бот для определения погоды.", reply_markup=get_main_keyboard(is_admin))

@dp.message(F.text == "Пользователи")
async def show_users(message: Message):
    if str(message.from_user.id) != ADMIN_ID:
        await message.answer("У вас нет доступа к этой команде.")
        return

    users = await get_users()

    if not users:
        await message.answer("Нет зарегистрированных пользователей.")
        return

    output = "👥 Список пользователей:\n\n"
    for user in users:
        telegram_id, username, gender, time, freq = user
        output += (
            f"Telegram ID: {telegram_id}\n"
            f"Имя: {username or 'не указано'}\n"
            f"Пол: {gender}\n"
            f"Время уведомления: {time}\n"
            f"Частота: {freq}\n"
            "--------------------\n"
        )

    if len(output) > 4096:
        for chunk in [output[i:i + 4096] for i in range(0, len(output), 4096)]:
            await message.answer(chunk)
    else:
        await message.answer(output)

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
    await message.answer("Вы успешно зарегистрированы!", reply_markup=get_main_keyboard())
    await state.clear()
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())