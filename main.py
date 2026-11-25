import asyncio
import json
import random
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command

# --- БАЗА ДАННЫХ ---
DB_FILE = "database.json"
def load_db():
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {}
def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

# --- КОНФИГ ---
BOT_TOKEN = 'ТОКЕН_БОТА'  # Сюда вставь токен от BotFather
WEBAPP_URL = "https://ТВОЙ_НИК.github.io/casewin-miniapp/" # Ссылка на GitHub Pages

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- КОМАНДА /start ---
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    db = load_db()
    
    if user_id not in db:
        db[user_id] = {"balance": 1000, "inventory": []}
        save_db(db)
        bonus_text = "\n🎁 Тебе начислено 1000 WC за первый вход!"
    else:
        bonus_text = ""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Открыть CaseWin", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])

    await message.answer(
        f"Привет, {message.from_user.first_name}!\n"
        f"Твой баланс: {db[user_id]['balance']} WC.{bonus_text}\n\n"
        f"Нажми кнопку ниже, чтобы открыть кейсы!",
        reply_markup=kb
    )

# --- АДМИН КОМАНДА ДЛЯ ТЕСТА БАЛАНСА ---
# Использование в чате с ботом: /add_wc 100000
@dp.message(Command("add_wc"))
async def add_wc(message: Message):
    user_id = str(message.from_user.id)
    db = load_db()
    if user_id not in db: return
    
    try:
        amount = int(message.text.split()[1])
        db[user_id]['balance'] += amount
        save_db(db)
        await message.answer(f"✅ Начислено {amount} WC. Твой баланс: {db[user_id]['balance']} WC")
    except:
        await message.answer("❌ Ошибка. Пиши так: /add_wc 100000")

# --- ЛОГИКА ОТКРЫТИЯ КЕЙСА ---
async def open_case(user_id: str, case_price: int):
    db = load_db()
    if user_id not in db: return "Ошибка: пользователь не найден."
    
    if db[user_id]['balance'] < case_price:
        return "Недостаточно Win Coins! Пополни баланс."

    db[user_id]['balance'] -= case_price
    
    # УМНЫЕ ШАНСЫ (Зависят от цены кейса)
    roll = random.randint(1, 10000) # 10000 для высокой точности (0.01%)
    
    if case_price < 1000: # Дешевые кейсы (до 999)
        if roll <= 8000: prize, val = "AK-47 | Redline", 150
        elif roll <= 9800: prize, val = "AWP | Asiimov", 800
        else: prize, val = "Karambit | Doppler", 5000
        
    elif case_price < 15000: # Средние кейсы (от 1к до 15к)
        if roll <= 7500: prize, val = "M4A4 | Howl", 1200
        elif roll <= 9500: prize, val = "Butterfly | Fade", 4000
        elif roll <= 9950: prize, val = "Karambit | Doppler", 15000
        else: prize, val = "Sport Gloves | Pandora", 50000
        
    else: # Элитные кейсы (Драгон Лор, Легендарный)
        if roll <= 8500: prize, val = "Karambit | Doppler", 20000
        elif roll <= 9800: prize, val = "Sport Gloves | Pandora", 80000
        elif roll <= 9990: prize, val = "AWP | Dragon Lore", 150000
        else: prize, val = "M4A4 | Howl (StatTrak)", 300000 # Джекпот!

    db[user_id]['inventory'].append({"name": prize, "value": val})
    save_db(db)

    return f"🎉 Ты выбил: {prize}\n💰 Стоимость скина: {val} WC!"

# --- ЗАПУСК ---
async def main():
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
