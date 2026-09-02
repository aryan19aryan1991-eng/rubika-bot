import threading
import time
import random
import json
import os
import requests
from flask import Flask

TOKEN = "CDDFFF0VIIVCOGXRMOTCVJXZOWSMKMGISHMVNVUYTUDWZRAVFTGPPQXJZHDKTKYA"
BASE = "https://botapi.rubika.ir/v3/" + TOKEN

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "balances.json")
START_BALANCE = 100000

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def load_balances():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_balances(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def get_balance(data, chat_id):
    if chat_id not in data:
        data[chat_id] = START_BALANCE
    return data[chat_id]

def parse_amount(word):
    word = word.strip()
    multiplier = 1
    if word.endswith("کا") or word.endswith("k") or word.endswith("K"):
        multiplier = 1000
        word = word[:-2] if word.endswith("کا") else word[:-1]
    try:
        return int(float(word) * multiplier)
    except ValueError:
        return None

def send(chat_id, text):
    requests.post(BASE + "/sendMessage", json={"chat_id": chat_id, "text": text})

def bot_loop():
    balances = load_balances()
    print("بات روشن شد و منتظر پیامه...")
    offset_id = None

    while True:
        try:
            payload = {}
            if offset_id:
                payload["offset_id"] = offset_id

            res = requests.post(BASE + "/getUpdates", json=payload).json()
            updates = res.get("data", {}).get("updates", [])

            for u in updates:
                offset_id = u.get("new_message", {}).get("message_id") or offset_id
                chat_id = u.get("chat_id")
                text = u.get("new_message", {}).get("text", "")

                if not chat_id or not text:
                    continue

                parts = text.strip().split()

                if text.strip() in ("/start", "شروع"):
                    bal = get_balance(balances, chat_id)
                    save_balances(balances)
                    send(chat_id, "به بازی سکه خوش اومدی!\nموجودی فعلی: " + str(bal) + "\n\nبرای شرط‌بندی بنویس:\nراست 5کا\nیا\nچپ 1000")
                    continue

                if len(parts) == 2 and parts[0] in ("چپ", "راست"):
                    choice = parts[0]
                    amount = parse_amount(parts[1])
                    bal = get_balance(balances, chat_id)

                    if amount is None or amount <= 0:
                        send(chat_id, "مقدار شرط رو درست بنویس. مثال: راست 5کا")
                        continue

                    if amount > bal:
                        send(chat_id, "موجودی کافی نداری.\nموجودی فعلی: " + str(bal))
                        continue

                    result = random.choice(["چپ", "راست"])
                    win = (result == choice)

                    if win:
                        bal += amount
                        msg = "✅ بردی!\nحدس شما: " + choice + "\nنتیجه: " + result + "\nمقدار شرط: " + str(amount) + "\nموجودی جدید: " + str(bal)
                    else:
                        bal -= amount
                        msg = "❌ متاسفانه باختی\nحدس شما: " + choice + "\nنتیجه: " + result + "\nمقدار شرط: " + str(amount) + "\nموجودی جدید: " + str(bal)

                    balances[chat_id] = bal
                    save_balances(balances)
                    send(chat_id, msg)
                    continue

                send(chat_id, "برای شرط‌بندی بنویس:\nراست 5کا\nیا\nچپ 1000")

            time.sleep(3)

        except Exception as e:
            print("خطا:", e)
            time.sleep(3)

if __name__ == "__main__":
    t = threading.Thread(target=bot_loop, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
