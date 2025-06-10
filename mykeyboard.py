# from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
# from aiogram.types import KeyboardButton, InlineKeyboardButton

# # Основная клавиатура
# def get_main_keyboard(is_admin: bool = False):
#     builder = ReplyKeyboardBuilder()
#     builder.add(KeyboardButton(text="Узнать погоду"))
#     builder.add(KeyboardButton(text="Регистрация"))
#     if is_admin:
#         builder.add(KeyboardButton(text="Пользователи"))
#     return builder.as_markup(resize_keyboard=True)

# # Кнопки выбора пола
# def gender_keyboard():
#     builder = ReplyKeyboardBuilder()
#     builder.add(KeyboardButton(text="Мужской"))
#     builder.add(KeyboardButton(text="Женский"))
#     return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

# # Inline-клавиатура для часов
# def time_hour_keyboard():
#     builder = InlineKeyboardBuilder()
#     for hour in range(0, 24):
#         builder.add(InlineKeyboardButton(text=str(hour), callback_data=f"hour_{hour}"))
#     builder.adjust(4)
#     return builder.as_markup()

# # Inline-клавиатура для минут
# def time_minute_keyboard():
#     builder = InlineKeyboardBuilder()
#     for minute in range(0, 60, 5):
#         builder.add(InlineKeyboardButton(text=str(minute), callback_data=f"minute_{minute}"))
#     builder.adjust(5)
#     return builder.as_markup()


from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Основная клавиатура
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

# Функция получения эмодзи для погоды
def get_weather_smile(temp_c):
    if temp_c < 0:
        return "❄️"
    elif 0 <= temp_c < 15:
        return "🧥"
    elif 15 <= temp_c < 25:
        return "🌤️"
    else:
        return "🔥"
