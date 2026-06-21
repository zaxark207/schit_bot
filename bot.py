import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== ТОКЕН =====
TOKEN = "8904295863:AAGEfASNLj2dkyZJs2JnoPrL9OiI3DfUgaU"
bot = telebot.TeleBot(TOKEN)

# ===== ТАБЛИЦА ЦЕН =====
PRICES = {
    "Бук": {
        (260, 990):   {"AB": 180000, "BB": 175000, "BC": 170000},
        (1000, 1990): {"AB": 220000, "BB": 200000, "BC": 190000},
        (2000, 3000): {"AB": 250000, "BB": 175000, "BC": 220000},
    },
    "Дуб": {
        (260, 990):   {"AB": 210000, "BB": 205000, "BC": 200000},
        (1000, 1990): {"AB": 290000, "BB": 270000, "BC": 230000},
        (2000, 3000): {"AB": 330000, "BB": 300000, "BC": 280000},
    },
    "Ясень": {
        (260, 990):   {"AB": 205000, "BB": 200000, "BC": 195000},
        (1000, 1990): {"AB": 280000, "BB": 255000, "BC": 225000},
        (2000, 3000): {"AB": 325000, "BB": 295000, "BC": 275000},
    },
}

user_data = {}

def get_range(length):
    for low, high in [(260, 990), (1000, 1990), (2000, 3000)]:
        if low <= length <= high:
            return (low, high)
    return None

@bot.message_handler(commands=['start'])
def start(message):
    user_data[message.chat.id] = {}
    markup = InlineKeyboardMarkup()
    for wood in PRICES.keys():
        markup.add(InlineKeyboardButton(wood, callback_data=f"wood_{wood}"))
    bot.send_message(message.chat.id, "🌳 Выберите породу:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("wood_"):
        wood = data.split("_")[1]
        user_data[chat_id]["wood"] = wood
        bot.send_message(chat_id, "📏 Введите длину (в мм):")
    
    elif data.startswith("grade_"):
        grade = data.split("_")[1]
        user_data[chat_id]["grade"] = grade
        calculate_price(chat_id)

    elif data == "new_calc":
        start(call.message)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if chat_id not in user_data:
        start(message)
        return

    if "wood" not in user_data[chat_id]:
        start(message)
        return

    if "length" not in user_data[chat_id]:
        try:
            length = float(text)
            if get_range(length) is None:
                bot.send_message(chat_id, "❌ Длина должна быть от 260 до 3000 мм. Введите заново:")
                return
            user_data[chat_id]["length"] = length
            bot.send_message(chat_id, "📏 Введите ширину (в мм):")
        except:
            bot.send_message(chat_id, "❌ Введите число, например 560")
    
    elif "width" not in user_data[chat_id]:
        try:
            user_data[chat_id]["width"] = float(text)
            bot.send_message(chat_id, "📏 Введите толщину (в мм):")
        except:
            bot.send_message(chat_id, "❌ Введите число, например 20")
    
    elif "thickness" not in user_data[chat_id]:
        try:
            user_data[chat_id]["thickness"] = float(text)
            markup = InlineKeyboardMarkup()
            for grade in ["AB", "BB", "BC"]:
                markup.add(InlineKeyboardButton(grade, callback_data=f"grade_{grade}"))
            bot.send_message(chat_id, "🏷️ Выберите сорт:", reply_markup=markup)
        except:
            bot.send_message(chat_id, "❌ Введите число")

def calculate_price(chat_id):
    data = user_data[chat_id]
    wood = data["wood"]
    length = data["length"]
    width = data["width"]
    thickness = data["thickness"]
    grade = data["grade"]

    range_key = get_range(length)
    if range_key is None:
        bot.send_message(chat_id, "❌ Ошибка диапазона")
        return

    cube_price_no_nds = PRICES[wood][range_key][grade]
    cube_price_with_nds = cube_price_no_nds * 1.22

    volume = (length / 1000) * (width / 1000) * (thickness / 1000)
    piece_price_no_nds = volume * cube_price_no_nds
    piece_price_with_nds = volume * cube_price_with_nds
    pieces_in_cube = 1 / volume

    response = (
        f"✅ Порода: {wood}\n"
        f"📏 Размер: {int(length)}×{int(width)}×{int(thickness)} мм\n"
        f"📊 Диапазон длины: {range_key[0]}–{range_key[1]} мм\n"
        f"🏷️ Сорт: {grade}\n"
        f"━━━━━━━━━━━━\n"
        f"💰 Цена куба (без НДС): {cube_price_no_nds:,.0f} руб.\n"
        f"🧾 НДС 22%: {cube_price_no_nds * 0.22:,.0f} руб.\n"
        f"💰 Цена куба (с НДС): {cube_price_with_nds:,.0f} руб.\n"
        f"━━━━━━━━━━━━\n"
        f"📐 Объём: {volume:.4f} м³\n"
        f"💵 Цена за щит (без НДС): {piece_price_no_nds:.2f} руб.\n"
        f"💰 Цена за щит (с НДС): {piece_price_with_nds:.2f} руб.\n"
        f"📦 Штук в кубе: {pieces_in_cube:.1f} шт."
    )

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔄 Рассчитать ещё", callback_data="new_calc"))
    bot.send_message(chat_id, response, reply_markup=markup)

print("Бот запущен...")
bot.polling()
