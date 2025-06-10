# bot.py
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import requests
from config import BOT_TOKEN, WEATHER_API_KEY, ADMIN_ID
from database import get_users, init_db, add_or_update_user, get_user

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- FSM для регистрации ---
class Registration(StatesGroup):
    gender = State()
    notification_hour = State()
    notification_minute = State()
    notification_freq = State()

# --- INLINE КНОПКИ ---

def get_main_inline_keyboard(is_admin=False):
    buttons = [
        [InlineKeyboardButton(text="Узнать погоду", callback_data="weather")],
        [InlineKeyboardButton(text="Регистрация", callback_data="register")]
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton(text="Пользователи", callback_data="users")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

gender_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Мужской", callback_data="gender_male"),
     InlineKeyboardButton(text="Женский", callback_data="gender_female")]
])

def get_hour_kb():
    buttons = []
    row = []
    for h in range(0, 24):
        row.append(InlineKeyboardButton(text=str(h), callback_data=f"hour_{h}"))
        if len(row) == 6:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_minute_kb():
    buttons = []
    row = []
    for m in range(0, 60, 5):
        row.append(InlineKeyboardButton(text=str(m), callback_data=f"minute_{m}"))
        if len(row) == 6:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- СМАЙЛИКИ ПОГОДЫ ---
def get_weather_smile(temp_c):
    if temp_c < 0:
        return "❄️"
    elif 0 <= temp_c < 15:
        return "🧥"
    elif 15 <= temp_c < 25:
        return "🌤️"
    else:
        return "🔥"

# --- ОСНОВНЫЕ ХЕНДЛЕРЫ ---

@dp.message(F.text)
async def start(message: Message):
    await message.delete()  # удаляем текстовые сообщения, если не нужны
    is_admin = message.from_user.id == int(ADMIN_ID)
    await bot.send_message(
        chat_id=message.chat.id,
        text="Привет! Я бот для определения погоды.",
        reply_markup=get_main_inline_keyboard(is_admin)
    )

# --- INLINE HANDLERS ---
@dp.callback_query(F.data == "weather")
async def get_weather(callback: CallbackQuery):
    url = f"https://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q=Moscow"
    response = requests.get(url)
    data = response.json()

    if "error" in data:
        await callback.answer("Ошибка получения погоды.", show_alert=True)
        return

    temp_c = data["current"]["temp_c"]
    emoji = get_weather_smile(temp_c)
    await callback.message.edit_text(f"{emoji} Температура в Москве: {temp_c}°C", reply_markup=get_main_inline_keyboard())

@dp.callback_query(F.data == "users")
async def show_users(callback: CallbackQuery):
    if str(callback.from_user.id) != ADMIN_ID:
        await callback.answer("У вас нет доступа к этой команде.", show_alert=True)
        return

    users = await get_users()
    output = "👥 Список пользователей:\n\n"
    if not users:
        await callback.message.edit_text("Нет зарегистрированных пользователей.", reply_markup=get_main_inline_keyboard())
        return

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
        parts = [output[i:i + 4096] for i in range(0, len(output), 4096)]
        await callback.message.edit_text(parts[0])
        for part in parts[1:]:
            await bot.send_message(callback.message.chat.id, part)
    else:
        await callback.message.edit_text(output, reply_markup=get_main_inline_keyboard())

    await callback.answer()

@dp.callback_query(F.data == "register")
async def registration_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Registration.gender)
    await callback.message.edit_text("Выберите ваш пол:", reply_markup=gender_kb)

# --- ГЕНДЕР --- 
@dp.callback_query(F.data.startswith("gender_"))
async def registration_gender(callback: CallbackQuery, state: FSMContext):
    gender = "Мужской" if callback.data == "gender_male" else "Женский"
    await state.update_data(gender=gender)
    await state.set_state(Registration.notification_hour)
    await callback.message.edit_text("Выберите час уведомления:", reply_markup=get_hour_kb())

# --- ЧАС ---
@dp.callback_query(F.data.startswith("hour_"))
async def registration_hour(callback: CallbackQuery, state: FSMContext):
    hour = callback.data.split("_")[1]
    await state.update_data(notification_hour=hour)
    await state.set_state(Registration.notification_minute)
    await callback.message.edit_text("Выберите минуты уведомления:", reply_markup=get_minute_kb())

# --- МИНУТЫ ---
@dp.callback_query(F.data.startswith("minute_"))
async def registration_minute(callback: CallbackQuery, state: FSMContext):
    minute = callback.data.split("_")[1]
    await state.update_data(notification_minute=minute)
    await state.set_state(Registration.notification_freq)
    await callback.message.edit_text("Введите частоту уведомлений (например, ежедневно или еженедельно):")

# --- ЧАСТОТА ---
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
    await message.delete()
    await bot.send_message(
        chat_id=message.chat.id,
        text="Вы успешно зарегистрированы!",
        reply_markup=get_main_inline_keyboard()
    )
    await state.clear()

# --- MAIN ---
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())