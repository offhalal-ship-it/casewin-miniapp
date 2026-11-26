import asyncio
import json
import random
import os
import requests
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from aiogram import Bot, Dispatcher
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command

# --- КОНФИГ ---
# Если на Koyeb добавлена переменная окружения BOT_TOKEN, он возьмет её. Иначе возьмет эту строку.
BOT_TOKEN = os.getenv("BOT_TOKEN", "СЮДА_ВСТАВЬ_ТОКЕН_ЕСЛИ_ЛОКАЛЬНО") 
WEBAPP_URL = "https://ТВОЙ_НИК.github.io/casewin-miniapp/" # Твоя ссылка GitHub

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

app = Flask(__name__)
CORS(app) # Разрешаем запросы с сайта

# --- БАЗА ДАННЫХ ---
DB_FILE = "database.json"
def load_db():
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {}
def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

# --- БАЗА СКИНОВ ---
SKINS_FILE = "skins_db.json"
VALID_SKINS = []
def download_skins():
    global VALID_SKINS
    if not os.path.exists(SKINS_FILE):
        print("Скачиваем базу скинов...")
        try:
            url = "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/skins.json"
            res = requests.get(url)
            with open(SKINS_FILE, "w", encoding="utf-8") as f:
                f.write(res.text)
        except Exception as e:
            print(f"Ошибка скачивания: {e}")
            return
    with open(SKINS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        VALID_SKINS = [s for s in data if s.get("image")]

download_skins()

# --- API ДЛЯ ОТКРЫТИЯ КЕЙСА ---
@app.route('/api/open_case', methods=['POST'])
def api_open_case():
    data = request.json
    user_id = str(data.get('user_id'))
    case_price = int(data.get('case_price'))
    
    db = load_db()
    if user_id not in db: return jsonify({"error": "Юзер не найден"}), 404
    if db[user_id]['balance'] < case_price: return jsonify({"error": "Недостаточно WC"}), 400

    # Списываем баланс
    db[user_id]['balance'] -= case_price
    
    # --- МАТЕМАТИКА ШАНСОВ (70% СЛИВ) ---
    roll = random.randint(1, 1000)
    if roll <= 700:
        target_price = int(case_price * random.uniform(0.05, 0.30))
        allowed = ["Mil-Spec Grade", "Restricted"]
    elif roll <= 900:
        target_price = int(case_price * random.uniform(0.50, 0.90))
        allowed = ["Restricted", "Classified"]
    elif roll <= 990:
        target_price = int(case_price * random.uniform(1.5, 3.0))
        allowed = ["Classified", "Covert"]
    else:
        target_price = int(case_price * random.uniform(5.0, 30.0))
        allowed = ["Covert", "Contraband", "★"]

    # Выбираем скин
    pool = [s for s in VALID_SKINS if s.get('rarity') and any(r in s['rarity']['name'] for r in allowed)]
    winner = random.choice(pool) if pool else random.choice(VALID_SKINS)
    
    # Записываем в инвентарь
    db[user_id]['inventory'].append({"name": winner['name'], "price": target_price, "img": winner['image']})
    save_db(db)

    return jsonify({
        "success": True, 
        "new_balance": db[user_id]['balance'], 
        "skin": winner['name'], 
        "price": target_price, 
        "img": winner['image']
    })

@dp.message(CommandStart())
async def cmd_start(message: Message):
    uid = str(message.from_user.id)
    db = load_db()
    if uid not in db: 
        db[uid] = {"balance": 1000, "inventory": []}
        save_db(db)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚀 Открыть CaseWin", web_app=WebAppInfo(url=WEBAPP_URL))]])
    await message.answer(f"Привет! Твой баланс: {db[uid]['balance']} WC.", reply_markup=kb)

@dp.message(Command("add_wc"))
async def add_wc(message: Message):
    uid = str(message.from_user.id)
    db = load_db()
    try:
        amount = int(message.text.split()[1])
        db[uid]['balance'] += amount
        save_db(db)
        await message.answer(f"✅ Начислено {amount} WC. Баланс: {db[uid]['balance']}")
    except: pass

# --- ЗАПУСК БОТА В ФОНЕ (для Koyeb) ---
def start_bot():
    asyncio.run(dp.start_polling(bot))

threading.Thread(target=start_bot, daemon=True).start()

# Этот блок нужен только если запускать локально
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
