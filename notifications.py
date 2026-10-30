import requests

BOT_TOKEN = "8294946961:AAFfr6tWQk_dLcdCyw_G7kAQUsdyCpQyywE"
CHAT_ID = "-1003720172728"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload, timeout=5)
        return response.json()
    except Exception as e:
        print("Telegram Notification Error:", e)
        return None

def send_product_photo(image_url, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "photo": image_url,
                "caption": caption
            },
            timeout=5
        )
        return response.json()
    except Exception as e:
        print("Photo Notification Error:", e)
        return None
