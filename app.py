import email
from enum import unique
from sys import modules
from flask import render_template, redirect, url_for
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from datetime import datetime
# Add this near the top of app.py with other imports
from datetime import datetime
import uuid
import requests
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

BOT_TOKEN = "8294946961:AAFfr6tWQk_dLcdCyw_G7kAQUsdyCpQyywE"

# IMPORTANT:
# Replace with your REAL group ID
CHAT_ID = "-1003720172728"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": -1003720172728,
        "text": message,
        "parse_mode": "HTML"
    }
    try:

        response = requests.post(
            url,
            data=payload
        )

        print("Telegram Response:")
        print(response.text)

        return response.json()

    except Exception as e:

        print("Telegram Error:", e)

        return None
def send_product_photo(image_url, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        response = requests.post(
            url,
            data={
                "chat_id": -1003720172728,
                "photo": image_url,
                "caption": caption
            }
        )
        print("Photo Response:")
        print(response.text)
        return response.json()
    except Exception as e:
        print("Photo Error:", e)
        return None

app = Flask(__name__)
app.secret_key = 'mobile_shop_secret_key_2024'

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    profile= db.Column(db.String(128), nullable=False)

# Update the USERS dictionary to include order history
USERS = {
    "admin@mobishop.com": {
        "email": "admin@mobishop.com",
        "password": "admin123",
        "name": "Admin User",
        "role": "admin",
        "created_at": "2025-01-01",
        "orders": []
    }
}
PRODUCTS = [
    # ========== APPLE PRODUCTS (10 products) ==========
    {
        "id": 1,
        "name": "iPhone 15 Pro Max",
        "brand": "Apple",
        "price": 1199,
        "original_price": 1299,
        "discount": 8,
        "rating": 4.9,
        "reviews": 1234,
        "image": "https://i.pinimg.com/1200x/05/5a/29/055a294e8b96aab43b38c5ef762d0555.jpg",
        "colors": ["Natural Titanium", "Blue Titanium", "White Titanium", "Black Titanium"],
        "storage": ["256GB", "512GB", "1TB"],
        "is_new": True,
        "featured": True,
        "stock": 45
    },
    {
        "id": 2,
        "name": "iPhone 15 Pro",
        "brand": "Apple",
        "price": 999,
        "original_price": 1099,
        "discount": 9,
        "rating": 4.8,
        "reviews": 987,
        "image": "https://i.pinimg.com/736x/17/e1/a5/17e1a575a8369f7e8fad1732af55280c.jpg",
        "colors": ["Natural Titanium", "Blue Titanium", "White Titanium"],
        "storage": ["128GB", "256GB", "512GB"],
        "is_new": True,
        "featured": True,
        "stock": 52
    },
    {
        "id": 3,
        "name": "iPhone 15 Plus",
        "brand": "Apple",
        "price": 899,
        "original_price": 999,
        "discount": 10,
        "rating": 4.7,
        "reviews": 756,
        "image": "https://i.pinimg.com/1200x/7e/58/bc/7e58bc3a3797c3220478eb2dad0d9842.jpg",
        "colors": ["Pink", "Yellow", "Green", "Blue", "Black"],
        "storage": ["128GB", "256GB", "512GB"],
        "is_new": True,
        "featured": False,
        "stock": 38
    },
    {
        "id": 4,
        "name": "iPhone 15",
        "brand": "Apple",
        "price": 799,
        "original_price": 899,
        "discount": 11,
        "rating": 4.7,
        "reviews": 892,
        "image": "https://i.pinimg.com/1200x/64/24/18/6424184a64ed588c3283f138b3053a69.jpg",
        "colors": ["Pink", "Yellow", "Green", "Blue", "Black"],
        "storage": ["128GB", "256GB"],
        "is_new": True,
        "featured": False,
        "stock": 67
    },
    {
        "id": 5,
        "name": "iPhone 14 Pro Max",
        "brand": "Apple",
        "price": 999,
        "original_price": 1199,
        "discount": 17,
        "rating": 4.8,
        "reviews": 2345,
        "image": "https://i.pinimg.com/1200x/01/40/b3/0140b387346663478a324b689b922e1d.jpg",
        "colors": ["Deep Purple", "Gold", "Silver", "Space Black"],
        "storage": ["128GB", "256GB", "512GB", "1TB"],
        "is_new": False,
        "featured": True,
        "stock": 23
    },
    {
        "id": 6,
        "name": "iPhone 14 Pro",
        "brand": "Apple",
        "price": 899,
        "original_price": 1099,
        "discount": 18,
        "rating": 4.7,
        "reviews": 1876,
        "image": "https://i.pinimg.com/736x/66/02/be/6602be19dcd832cb13cb2481a683dbf7.jpg",
        "colors": ["Deep Purple", "Gold", "Silver", "Space Black"],
        "storage": ["128GB", "256GB", "512GB", "1TB"],
        "is_new": False,
        "featured": False,
        "stock": 31
    },
    {
        "id": 7,
        "name": "iPhone 17 Pro Max",
        "brand": "Apple",
        "price": 1549,
        "original_price": 1899,
        "discount": 17,
        "rating": 4.6,
        "reviews": 1234,
        "image": "https://i.pinimg.com/1200x/d8/35/c3/d835c3944ca58d05e142b396f18a146c.jpg",
        "colors": ["Blue", "Purple", "Yellow", "Midnight", "Starlight"],
        "storage": ["128GB", "256GB", "512GB"],
        "is_new": False,
        "featured": False,
        "stock": 44
    },
    {
        "id": 8,
        "name": "iPhone 14",
        "brand": "Apple",
        "price": 699,
        "original_price": 799,
        "discount": 13,
        "rating": 4.6,
        "reviews": 2156,
        "image": "https://i.pinimg.com/1200x/74/81/1f/74811f31ccd7fb57928c26b068e2e3ba.jpg",
        "colors": ["Blue", "Purple", "Yellow", "Midnight", "Starlight"],
        "storage": ["128GB", "256GB", "512GB"],
        "is_new": False,
        "featured": False,
        "stock": 56
    },
    {
        "id": 9,
        "name": "iPhone SE (3rd Gen)",
        "brand": "Apple",
        "price": 429,
        "original_price": 499,
        "discount": 14,
        "rating": 4.5,
        "reviews": 876,
        "image": "https://i.pinimg.com/1200x/d4/40/29/d44029329918b28adb18b3a5ac644806.jpg",
        "colors": ["Midnight", "Starlight", "Product RED"],
        "storage": ["64GB", "128GB", "256GB"],
        "is_new": False,
        "featured": False,
        "stock": 89
    },
    {
        "id": 10,
        "name": "iPhone 13 Pro Max",
        "brand": "Apple",
        "price": 799,
        "original_price": 1099,
        "discount": 27,
        "rating": 4.7,
        "reviews": 3456,
        "image": "https://i.pinimg.com/1200x/aa/d5/67/aad567c4c481909bee3ce3837550a7db.jpg",
        "colors": ["Sierra Blue", "Graphite", "Gold", "Silver"],
        "storage": ["128GB", "256GB", "512GB", "1TB"],
        "is_new": False,
        "featured": False,
        "stock": 12
    },

    # ========== SAMSUNG PRODUCTS (10 products) ==========
    {
        "id": 11,
        "name": "Samsung Galaxy S24 Ultra",
        "brand": "Samsung",
        "price": 1299,
        "original_price": 1399,
        "discount": 7,
        "rating": 4.9,
        "reviews": 2345,
        "image": "https://i.pinimg.com/736x/6f/b2/6e/6fb26e46cd195696459eee7c8ff6f4d1.jpg",
        "colors": ["Titanium Gray", "Titanium Black", "Titanium Violet", "Titanium Yellow"],
        "storage": ["256GB", "512GB", "1TB"],
        "is_new": True,
        "featured": True,
        "stock": 34
    },
    {
        "id": 12,
        "name": "Samsung Galaxy S24 Plus",
        "brand": "Samsung",
        "price": 1099,
        "original_price": 1199,
        "discount": 8,
        "rating": 4.8,
        "reviews": 1876,
        "image": "https://i.pinimg.com/736x/aa/2f/29/aa2f29cb067e9ef16c17792fc493769c.jpg",
        "colors": ["Onyx Black", "Marble Gray", "Cobalt Violet", "Amber Yellow"],
        "storage": ["256GB", "512GB"],
        "is_new": True,
        "featured": True,
        "stock": 45
    },
    {
        "id": 13,
        "name": "Samsung Galaxy S24",
        "brand": "Samsung",
        "price": 799,
        "original_price": 899,
        "discount": 11,
        "rating": 4.7,
        "reviews": 1543,
        "image": "https://i.pinimg.com/736x/5e/67/e2/5e67e2436d4cab7808e890400c4ac126.jpg",
        "colors": ["Onyx Black", "Marble Gray", "Cobalt Violet", "Amber Yellow"],
        "storage": ["128GB", "256GB", "512GB"],
        "is_new": True,
        "featured": False,
        "stock": 67
    },
    {
        "id": 14,
        "name": "Samsung Galaxy Z Fold 5",
        "brand": "Samsung",
        "price": 1799,
        "original_price": 1899,
        "discount": 5,
        "rating": 4.8,
        "reviews": 987,
        "image": "https://i.pinimg.com/236x/96/75/94/9675945a9867c5d1ee937ed741269aa3.jpg",
        "colors": ["Icy Blue", "Phantom Black", "Cream"],
        "storage": ["512GB", "1TB"],
        "is_new": True,
        "featured": True,
        "stock": 23
    },
    {
        "id": 15,
        "name": "Samsung Galaxy Z Flip 5",
        "brand": "Samsung",
        "price": 999,
        "original_price": 1099,
        "discount": 9,
        "rating": 4.7,
        "reviews": 1234,
        "image": "https://i.pinimg.com/1200x/db/8f/0a/db8f0ac60f487fe988b2756ac0df6d8d.jpg",
        "colors": ["Mint", "Graphite", "Cream", "Lavender"],
        "storage": ["256GB", "512GB"],
        "is_new": True,
        "featured": True,
        "stock": 34
    },
    {
        "id": 16,
        "name": "Samsung Galaxy A55 5G",
        "brand": "Samsung",
        "price": 449,
        "original_price": 499,
        "discount": 10,
        "rating": 4.5,
        "reviews": 2345,
        "image": "https://i.pinimg.com/1200x/f1/eb/7b/f1eb7b2e9cdc57fa087030667e97debe.jpg",
        "colors": ["Awesome Iceblue", "Awesome Lilac", "Awesome Navy"],
        "storage": ["128GB", "256GB"],
        "is_new": True,
        "featured": False,
        "stock": 89
    },
    {
        "id": 17,
        "name": "Samsung Galaxy A35 5G",
        "brand": "Samsung",
        "price": 399,
        "original_price": 449,
        "discount": 11,
        "rating": 4.4,
        "reviews": 1876,
        "image": "https://i.pinimg.com/736x/5e/67/e2/5e67e2436d4cab7808e890400c4ac126.jpg",
        "colors": ["Awesome Iceblue", "Awesome Lilac"],
        "storage": ["128GB", "256GB"],
        "is_new": True,
        "featured": False,
        "stock": 112
    },
    {
        "id": 18,
        "name": "Samsung Galaxy S23 Ultra",
        "brand": "Samsung",
        "price": 949,
        "original_price": 1199,
        "discount": 21,
        "rating": 4.8,
        "reviews": 3456,
        "image": "https://i.pinimg.com/736x/6f/b2/6e/6fb26e46cd195696459eee7c8ff6f4d1.jpg",
        "colors": ["Phantom Black", "Green", "Cream", "Lavender"],
        "storage": ["256GB", "512GB", "1TB"],
        "is_new": False,
        "featured": False,
        "stock": 45
    },
    {
        "id": 19,
        "name": "Samsung Galaxy S23 Plus",
        "brand": "Samsung",
        "price": 799,
        "original_price": 999,
        "discount": 20,
        "rating": 4.7,
        "reviews": 2345,
        "image": "https://i.pinimg.com/736x/aa/2f/29/aa2f29cb067e9ef16c17792fc493769c.jpg",
        "colors": ["Phantom Black", "Green", "Cream", "Lavender"],
        "storage": ["256GB", "512GB"],
        "is_new": False,
        "featured": False,
        "stock": 56
    },
    {
        "id": 20,
        "name": "Samsung Galaxy A15 5G",
        "brand": "Samsung",
        "price": 199,
        "original_price": 249,
        "discount": 20,
        "rating": 4.3,
        "reviews": 876,
        "image": "https://i.pinimg.com/1200x/f1/eb/7b/f1eb7b2e9cdc57fa087030667e97debe.jpg",
        "colors": ["Blue Black", "Light Blue"],
        "storage": ["128GB"],
        "is_new": True,
        "featured": False,
        "stock": 156
    },

    # ========== OPPO PRODUCTS (8 products) ==========
    {
        "id": 21,
        "name": "OPPO Find X7 Ultra",
        "brand": "Oppo",
        "price": 1199,
        "original_price": 1299,
        "discount": 8,
        "rating": 4.8,
        "reviews": 567,
        "image": "https://i.pinimg.com/1200x/a4/43/37/a4433724bbc8c42b037b3976a1f39e70.jpg",
        "colors": ["Ocean Blue", "Black", "Silver"],
        "storage": ["256GB", "512GB", "1TB"],
        "is_new": True,
        "featured": True,
        "stock": 34
    },
    {
        "id": 22,
        "name": "OPPO Find N3 Flip",
        "brand": "Oppo",
        "price": 899,
        "original_price": 999,
        "discount": 10,
        "rating": 4.7,
        "reviews": 432,
        "image": "https://i.pinimg.com/1200x/45/53/70/4553703eec8d89f405455dff6f100086.jpg",
        "colors": ["Cream Gold", "Slim Black", "Rose Pink"],
        "storage": ["256GB", "512GB"],
        "is_new": True,
        "featured": True,
        "stock": 45
    },
    {
        "id": 23,
        "name": "OPPO Reno11 Pro",
        "brand": "Oppo",
        "price": 649,
        "original_price": 749,
        "discount": 13,
        "rating": 4.6,
        "reviews": 678,
        "image": "https://i.pinimg.com/736x/6c/40/48/6c4048026291c02f0ed21b5b879cad85.jpg",
        "colors": ["Pearl White", "Moss Green"],
        "storage": ["256GB", "512GB"],
        "is_new": True,
        "featured": False,
        "stock": 67
    },
    {
        "id": 24,
        "name": "OPPO Reno11",
        "brand": "Oppo",
        "price": 499,
        "original_price": 599,
        "discount": 17,
        "rating": 4.5,
        "reviews": 789,
        "image": "https://i.pinimg.com/736x/b2/ec/23/b2ec23a8affac26f542fc8e2c55dd261.jpg",
        "colors": ["Wave Green", "Rock Grey"],
        "storage": ["128GB", "256GB"],
        "is_new": True,
        "featured": False,
        "stock": 89
    },
    {
        "id": 25,
        "name": "OPPO Find X6 Pro",
        "brand": "Oppo",
        "price": 999,
        "original_price": 1199,
        "discount": 17,
        "rating": 4.7,
        "reviews": 543,
        "image": "https://i.pinimg.com/1200x/2a/eb/38/2aeb388a76d304ef66ce85003a7de41d.jpg",
        "colors": ["Black", "Brown", "Green"],
        "storage": ["256GB", "512GB"],
        "is_new": False,
        "featured": False,
        "stock": 23
    },
    {
        "id": 26,
        "name": "OPPO A98 5G",
        "brand": "Oppo",
        "price": 349,
        "original_price": 399,
        "discount": 13,
        "rating": 4.4,
        "reviews": 1234,
        "image": "https://i.pinimg.com/1200x/a4/43/37/a4433724bbc8c42b037b3976a1f39e70.jpg",
        "colors": ["Cool Black", "Dreamy Blue"],
        "storage": ["128GB", "256GB"],
        "is_new": True,
        "featured": False,
        "stock": 112
    },
    {
        "id": 27,
        "name": "OPPO A78 5G",
        "brand": "Oppo",
        "price": 249,
        "original_price": 299,
        "discount": 17,
        "rating": 4.3,
        "reviews": 987,
        "image": "https://i.pinimg.com/736x/6c/40/48/6c4048026291c02f0ed21b5b879cad85.jpg",
        "colors": ["Mist Black", "Glowing Purple"],
        "storage": ["128GB"],
        "is_new": False,
        "featured": False,
        "stock": 145
    },
    {
        "id": 28,
        "name": "OPPO K11x",
        "brand": "Oppo",
        "price": 229,
        "original_price": 279,
        "discount": 18,
        "rating": 4.2,
        "reviews": 765,
        "image": "https://i.pinimg.com/736x/b2/ec/23/b2ec23a8affac26f542fc8e2c55dd261.jpg",
        "colors": ["Glaze Blue", "Shadow Black"],
        "storage": ["128GB"],
        "is_new": True,
        "featured": False,
        "stock": 178
    },

    # ========== XIAOMI PRODUCTS (8 products) ==========
    {
        "id": 29,
        "name": "Xiaomi 14 Ultra",
        "brand": "Xiaomi",
        "price": 999,
        "original_price": 1199,
        "discount": 17,
        "rating": 4.8,
        "reviews": 987,
        "image": "https://i.pinimg.com/1200x/db/8f/0a/db8f0ac60f487fe988b2756ac0df6d8d.jpg",
        "colors": ["Black", "White", "Blue"],
        "storage": ["256GB", "512GB", "1TB"],
        "is_new": True,
        "featured": True,
        "stock": 45
    },
    {
        "id": 30,
        "name": "Xiaomi 14 Pro",
        "brand": "Xiaomi",
        "price": 799,
        "original_price": 899,
        "discount": 11,
        "rating": 4.7,
        "reviews": 876,
        "image": "https://i.pinimg.com/736x/e0/bf/be/e0bfbe214ad2b0a70a0c0af30b7b486c.jpg",
        "colors": ["Black", "Silver", "Titanium"],
        "storage": ["256GB", "512GB"],
        "is_new": True,
        "featured": True,
        "stock": 56
    },
    {
        "id": 31,
        "name": "Xiaomi 14",
        "brand": "Xiaomi",
        "price": 699,
        "original_price": 799,
        "discount": 13,
        "rating": 4.7,
        "reviews": 765,
        "image": "https://i.pinimg.com/736x/c6/a8/f8/c6a8f8194606dfee828a8b5a8f21ffce.jpg",
        "colors": ["Black", "White", "Jade Green"],
        "storage": ["256GB", "512GB"],
        "is_new": True,
        "featured": False,
        "stock": 78
    },
    {
        "id": 32,
        "name": "Xiaomi 13T Pro",
        "brand": "Xiaomi",
        "price": 599,
        "original_price": 699,
        "discount": 14,
        "rating": 4.6,
        "reviews": 1234,
        "image": "https://i.pinimg.com/1200x/af/f1/43/aff143262a0689ffe2957303366ac190.jpg",
        "colors": ["Alpine Blue", "Meadow Green", "Black"],
        "storage": ["256GB", "512GB"],
        "is_new": False,
        "featured": False,
        "stock": 67
    },
    {
        "id": 33,
        "name": "Xiaomi 13T",
        "brand": "Xiaomi",
        "price": 499,
        "original_price": 599,
        "discount": 17,
        "rating": 4.5,
        "reviews": 987,
        "image": "https://i.pinimg.com/736x/b7/31/28/b73128f2e826c6df8829a0f665b2b463.jpg",
        "colors": ["Alpine Blue", "Meadow Green"],
        "storage": ["128GB", "256GB"],
        "is_new": False,
        "featured": False,
        "stock": 89
    },
    {
        "id": 34,
        "name": "Xiaomi POCO F6 Pro",
        "brand": "Xiaomi",
        "price": 449,
        "original_price": 549,
        "discount": 18,
        "rating": 4.5,
        "reviews": 654,
        "image": "https://i.pinimg.com/736x/c6/a8/f8/c6a8f8194606dfee828a8b5a8f21ffce.jpg",
        "colors": ["Black", "White"],
        "storage": ["256GB", "512GB"],
        "is_new": True,
        "featured": False,
        "stock": 112
    },
    {
        "id": 35,
        "name": "Xiaomi Redmi Note 13 Pro",
        "brand": "Xiaomi",
        "price": 349,
        "original_price": 399,
        "discount": 13,
        "rating": 4.4,
        "reviews": 2345,
        "image": "https://i.pinimg.com/1200x/d4/40/29/d44029329918b28adb18b3a5ac644806.jpg",
        "colors": ["Midnight Black", "Forest Green", "Lavender Purple"],
        "storage": ["128GB", "256GB", "512GB"],
        "is_new": True,
        "featured": False,
        "stock": 156
    },
    {
        "id": 36,
        "name": "Xiaomi Redmi Note 13",
        "brand": "Xiaomi",
        "price": 249,
        "original_price": 299,
        "discount": 17,
        "rating": 4.3,
        "reviews": 1876,
        "image": "https://i.pinimg.com/1200x/db/8f/0a/db8f0ac60f487fe988b2756ac0df6d8d.jpg",
        "colors": ["Midnight Black", "Mint Green", "Ice Blue"],
        "storage": ["128GB", "256GB"],
        "is_new": True,
        "featured": False,
        "stock": 189
    },

    # ========== GOOGLE PIXEL PRODUCTS (8 products) ==========
    {
        "id": 37,
        "name": "Google Pixel 8 Pro",
        "brand": "Google",
        "price": 999,
        "original_price": 1099,
        "discount": 9,
        "rating": 4.8,
        "reviews": 1456,
        "image": "https://i.pinimg.com/736x/a3/33/98/a333985f50d57792b712cd42fd2270b2.jpg",
        "colors": ["Obsidian", "Porcelain", "Bay"],
        "storage": ["128GB", "256GB", "512GB"],
        "is_new": True,
        "featured": True,
        "stock": 56
    },
    {
        "id": 38,
        "name": "Google Pixel 8",
        "brand": "Google",
        "price": 699,
        "original_price": 799,
        "discount": 13,
        "rating": 4.7,
        "reviews": 1234,
        "image": "https://i.pinimg.com/1200x/ad/23/6a/ad236a8427fb0b6ed1aa3d8c17ec2a16.jpg",
        "colors": ["Obsidian", "Hazel", "Rose"],
        "storage": ["128GB", "256GB"],
        "is_new": True,
        "featured": True,
        "stock": 78
    },
    {
        "id": 39,
        "name": "Google Pixel 7 Pro",
        "brand": "Google",
        "price": 599,
        "original_price": 899,
        "discount": 33,
        "rating": 4.7,
        "reviews": 2345,
        "image": "https://i.pinimg.com/736x/24/69/6f/24696ff09256256d3da7eab858891a74.jpg",
        "colors": ["Obsidian", "Snow", "Hazel"],
        "storage": ["128GB", "256GB", "512GB"],
        "is_new": False,
        "featured": False,
        "stock": 45
    },
    {
        "id": 40,
        "name": "Google Pixel 7",
        "brand": "Google",
        "price": 449,
        "original_price": 599,
        "discount": 25,
        "rating": 4.6,
        "reviews": 1876,
        "image": "https://i.pinimg.com/1200x/88/f7/49/88f749ef1650a88de20e3e87d1d774c3.jpg",
        "colors": ["Obsidian", "Snow", "Lemongrass"],
        "storage": ["128GB", "256GB"],
        "is_new": False,
        "featured": False,
        "stock": 67
    },
    {
        "id": 41,
        "name": "Google Pixel Fold",
        "brand": "Google",
        "price": 1699,
        "original_price": 1799,
        "discount": 6,
        "rating": 4.7,
        "reviews": 543,
        "image": "https://i.pinimg.com/736x/0e/0d/a4/0e0da4d18aee0b4b612a07bbb7dd4df2.jpg",
        "colors": ["Obsidian", "Porcelain"],
        "storage": ["256GB", "512GB"],
        "is_new": True,
        "featured": True,
        "stock": 23
    },
    {
        "id": 42,
        "name": "Google Pixel 7a",
        "brand": "Google",
        "price": 399,
        "original_price": 499,
        "discount": 20,
        "rating": 4.5,
        "reviews": 987,
        "image": "https://i.pinimg.com/1200x/aa/d5/67/aad567c4c481909bee3ce3837550a7db.jpg",
        "colors": ["Charcoal", "Snow", "Sea", "Coral"],
        "storage": ["128GB"],
        "is_new": False,
        "featured": False,
        "stock": 89
    },
    {
        "id": 43,
        "name": "Google Pixel 6 Pro",
        "brand": "Google",
        "price": 499,
        "original_price": 899,
        "discount": 44,
        "rating": 4.5,
        "reviews": 3456,
        "image": "https://i.pinimg.com/1200x/ad/23/6a/ad236a8427fb0b6ed1aa3d8c17ec2a16.jpg",
        "colors": ["Stormy Black", "Cloudy White", "Sorta Sunny"],
        "storage": ["128GB", "256GB", "512GB"],
        "is_new": False,
        "featured": False,
        "stock": 34
    },
    {
        "id": 44,
        "name": "Google Pixel 6a",
        "brand": "Google",
        "price": 349,
        "original_price": 449,
        "discount": 22,
        "rating": 4.4,
        "reviews": 2345,
        "image": "https://i.pinimg.com/1200x/88/f7/49/88f749ef1650a88de20e3e87d1d774c3.jpg",
        "colors": ["Charcoal", "Chalk", "Sage"],
        "storage": ["128GB"],
        "is_new": False,
        "featured": False,
        "stock": 78
    }
]


def get_cart():
    if 'cart' not in session:
        session['cart'] = []
    return session['cart']


def save_cart(cart):
    session['cart'] = cart
    session.modified = True


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.context_processor
def utility_processor():
    def cart_count():
        cart = get_cart()
        return sum(item['quantity'] for item in cart)

    def is_logged_in():
        return 'user' in session

    def current_user():
        return session.get('user', {})

    def get_brands():
        return sorted(set(p['brand'] for p in PRODUCTS))

    return dict(cart_count=cart_count, is_logged_in=is_logged_in, current_user=current_user, get_brands=get_brands)


@app.route('/')
@app.route('/index')
def index():
    featured_products = [p for p in PRODUCTS if p.get('featured')][:8]
    new_products = [p for p in PRODUCTS if p.get('is_new')][:8]
    brands = sorted(set(p['brand'] for p in PRODUCTS))
    return render_template('front/index.html', featured_products=featured_products, new_products=new_products,
                           all_products=PRODUCTS, brands=brands)


@app.route('/shop')
def shop():
    brand = request.args.get('brand', '')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'default')

    products = PRODUCTS.copy()

    # Filter by brand
    if brand:
        products = [p for p in products if p['brand'].lower() == brand.lower()]

    # Filter by search
    if search:
        products = [p for p in products if search.lower() in p['name'].lower() or search.lower() in p['brand'].lower()]

    # Sort products
    if sort == 'price_low':
        products.sort(key=lambda x: x['price'])
    elif sort == 'price_high':
        products.sort(key=lambda x: x['price'], reverse=True)
    elif sort == 'rating':
        products.sort(key=lambda x: x['rating'], reverse=True)
    elif sort == 'newest':
        products.sort(key=lambda x: x['is_new'], reverse=True)

    # Get all unique brands
    brands = sorted(set(p['brand'] for p in PRODUCTS))

    return render_template('front/shop.html',
                           products=products,
                           brands=brands,
                           selected_brand=brand,
                           search_query=search,
                           selected_sort=sort)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = next(
        (p for p in PRODUCTS if p["id"] == product_id),
        None
    )

    if not product:
        flash("Product not found", "error")
        return redirect(url_for("shop"))

    # Related products
    related = [
                  p for p in PRODUCTS
                  if p["brand"] == product["brand"] and p["id"] != product_id
              ][:4]

    return render_template(
        "front/product-detail.html",
        product=product,
        related=related
    )


@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 1))
    color = request.form.get('color', '')
    storage = request.form.get('storage', '')

    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if not product:
        return jsonify({'success': False, 'message': 'Product not found'})

    cart = get_cart()

    # Check if item already in cart with same options
    for item in cart:
        if item['product_id'] == product_id and item.get('color') == color and item.get('storage') == storage:
            item['quantity'] += quantity
            save_cart(cart)
            return jsonify({'success': True, 'cart_count': sum(i['quantity'] for i in cart),
                            'message': f'Added another {quantity} {product["name"]} to cart'})

    cart.append({
        'product_id': product_id,
        'name': product['name'],
        'price': product['price'],
        'image': product['image'],
        'quantity': quantity,
        'color': color,
        'storage': storage
    })
    save_cart(cart)

    return jsonify({'success': True, 'cart_count': sum(i['quantity'] for i in cart),
                    'message': f'{product["name"]} added to cart'})


@app.route('/cart')
@login_required
def cart():
    cart = get_cart()
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    shipping = 0 if subtotal > 500 else 15
    tax = subtotal * 0.1
    total = subtotal + shipping + tax

    return render_template('front/cart.html', cart=cart, subtotal=subtotal, shipping=shipping, tax=tax, total=total)


@app.route('/order-confirmation')
@login_required
def order_confirmation():
    order = session.get('last_order')

    if not order:
        return redirect(url_for('index'))

    return render_template(
        'front/order-confirmation.html',
        order=order
    )


@app.route('/update-cart', methods=['POST'])
def update_cart():
    data = request.get_json()
    cart = get_cart()
    action = data.get('action')
    index = int(data.get('index'))
    if 0 <= index < len(cart):

        if action == 'increase':

            cart[index]['quantity'] += 1

        elif action == 'decrease':

            if cart[index]['quantity'] > 1:
                cart[index]['quantity'] -= 1

        elif action == 'remove':

            cart.pop(index)

    save_cart(cart)

    subtotal = sum(
        item['price'] * item['quantity']
        for item in cart
    )

    shipping = 0 if subtotal > 500 else 15
    tax = subtotal * 0.10
    total = subtotal + shipping + tax

    return jsonify({
        'success': True,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total
    })


@app.route('/checkout')
@login_required
def checkout():
    cart = get_cart()
    if not cart:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('shop'))

    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    shipping = 0 if subtotal > 500 else 15
    tax = subtotal * 0.1
    total = subtotal + shipping + tax

    return render_template('front/checkout.html', subtotal=subtotal, shipping=shipping, tax=tax, total=total)


@app.route('/place-order', methods=['POST'])
@login_required
def place_order():
    try:
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        city = request.form.get('city')
        payment_method = request.form.get('payment')

        if not all([fullname, email, phone, address, city, payment_method]):
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('checkout'))

        cart = get_cart()
        if not cart:
            flash('Cart is empty', 'warning')
            return redirect(url_for('cart'))
        order_id = 'ORD-' + str(uuid.uuid4())[:8].upper()
        subtotal = sum(
            item['price'] * item['quantity']
            for item in cart
        )
        shipping = 0 if subtotal > 500 else 15
        tax = subtotal * 0.1
        total = subtotal + shipping + tax

        order_data = {

            'order_id': order_id,

            'order_date':
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),

            'customer_name': fullname,
            'customer_email': email,
            'customer_phone': phone,
            'shipping_address': address,
            'city': city,
            'payment_method': payment_method,
            'items': cart,
            'subtotal': subtotal,
            'shipping': shipping,
            'tax': tax,
            'total': total,
            'status': 'Pending'
        }

        user_email = session['user']['email']
        if 'orders' not in USERS[user_email]:
            USERS[user_email]['orders'] = []
        USERS[user_email]['orders'].append(order_data)
        session['last_order'] = order_data

        # =========================
        # SEND PRODUCT IMAGES
        # =========================

        for item in cart:
            image_url = item.get('image')
            caption = f"""
                 {item['name']}
            """
            if image_url:
                send_product_photo(
                    image_url,
                    caption
                )
        products_text = ""
        for item in cart:
            products_text += f"""
        📦 <b>Phone:</b> {item['name']}
        🔢 <b>Qty:</b> {item['quantity']}
        💲 <b>Price:</b> ${item['price']:.2f}
        """
        telegram_message = f"""
        🛒 <b>NEW ORDER</b>
        ━━━━━━━━━━━━━━
        🆔 <b>Order ID:</b> {order_id}
        👤 <b>Full Name:</b> {fullname}
        📧 <b>Email:</b> {email}
        📞 <b>Phone Number:</b> {phone}
        🏠 <b>Address:</b> {address}
        🏙️ <b>City:</b> {city}
        💳 <b>Payment:</b> {payment_method.upper()}
        ━━━━━━━━━━━━━━
        <b>PRODUCTS</b>
        {products_text}
        ━━━━━━━━━━━━━━
        💰 <b>Subtotal:</b> ${subtotal:.2f}
        🚚 <b>Shipping:</b> ${shipping:.2f}
        🧾 <b>Tax:</b> ${tax:.2f}
        ━━━━━━━━━━━━━━
        💵 <b>TOTAL:</b> ${total:.2f}
        """
        send_telegram_message(telegram_message)
        session.pop('cart', None)
        flash(
            f'Order {order_id} placed successfully!',
            'success'
        )
        return redirect(
            url_for('order_confirmation')
        )
    except Exception as e:

        print(e)

        flash(
            'Order failed.',
            'danger'
        )

        return redirect(
            url_for('checkout')
        )


@app.route('/my-orders')
@login_required
def my_orders():
    user_email = session.get('user', {}).get('email')

    if not user_email:
        return redirect(url_for('login'))

    user_data = USERS.get(user_email, {})

    orders = user_data.get('orders', [])

    if not isinstance(orders, list):
        orders = []

    for order in orders:

        if not isinstance(order, dict):
            continue

        if 'items' not in order:
            order['items'] = []

        if not isinstance(order['items'], list):
            order['items'] = []

        order.setdefault('status', 'pending')
        order.setdefault('total', 0)
        order.setdefault('order_date', 'N/A')
        order.setdefault('shipping_address', '')
        order.setdefault('city', '')
        order.setdefault('payment_method', 'cash')

    return render_template(
        'front/my-orders.html',
        orders=orders
    )


@app.route('/order/<order_id>')
@login_required
def order_detail(order_id):
    user_email = session['user']['email']
    user_data = USERS.get(user_email, {})
    orders = user_data.get('orders', [])

    # Find the specific order
    order = next((o for o in orders if o['order_id'] == order_id), None)

    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('my_orders'))

    return render_template('front/order-detail.html', order=order)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        user = USERS.get(email)

        if user and user['password'] == password:
            session['user'] = {
                'email': user['email'],
                'name': user['name']
            }

            flash('Login successful', 'success')
            return redirect(url_for('index'))

        flash('Invalid email or password', 'error')

    return render_template('front/login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


@app.route('/create-user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validation
        if not name or not email or not password:
            flash('All fields are required', 'error')
            return render_template('front/create-user.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('front/create-user.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('front/create-user.html')

        if email in USERS:
            flash('Email already registered. Please login instead.', 'error')
            return render_template('front/create-user.html')

        # Create new user
        from datetime import datetime
        USERS[email] = {
            'email': email,
            'password': password,
            'name': name,
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'orders': []
        }

        # Auto-login after registration
        session['user'] = {
            'email': email,
            'name': name
        }

        flash(f'Account created successfully! Welcome {name}!', 'success')
        return redirect(url_for('index'))

    return render_template('front/create-user.html')


@app.route('/forget-pw', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'POST':
        email = request.form.get('email')

        if email in USERS:
            # In a real app, send password reset email
            # For demo, we'll just show a success message
            flash(f'Password reset link has been sent to {email} (Demo: Use password "demo123" to login)', 'success')

            # For demo purposes, we can also show the current password
            # In production, NEVER do this - send a reset link via email only
            if email == "demo@mobishop.com":
                flash('Demo account password is: demo123', 'info')
        else:
            flash('No account found with that email address', 'error')

    return render_template('front/forget-pw.html')


@app.route('/profile')
@login_required
def profile():
    user = session.get('user')
    user_data = USERS.get(user['email'], {})
    return render_template('front/profile.html', user=user_data)


@app.route("/admin/dashboard")
def admin_dashboard():
    module = "admin"
    return render_template("admin/dashboard/admin.html", module="admin")


@app.route("/admin/product")
def admin_product():
    module = "products"
    return render_template("admin/product/products.html", module="products")


@app.route("/admin/Phone")
def admin_Phone():
    module = "Phone"
    return render_template("admin/category/index.html", module="Phone")


@app.route("/admin/Phone/all")
def admin_Phone_all():
    return render_template("admin/Phone/all.html", module="all")


@app.route("/admin/Phone/Add")
def admin_Phone_Add():
    return render_template("admin/Phone/Add.html", module="add")


@app.route("/admin/Phone/brand")
def admin_Phone_brand():
    return render_template("admin/Phone/brand.html", module="brand")


@app.route("/admin/orders")
def admin_orders():
    module = "orders"
    return render_template("admin/order/orders.html", module="orders")


@app.route("/admin/users")
def admin_user():
    return render_template("admin/user/users.html",module="users")


@app.route("/admin/users")
def admin_users():
    module = "users"
    return render_template("admin/user/users.html", module="users")


@app.route("/admin/user/add")
def admin_user_add():
    return render_template("admin/user/add.html")


@app.route("/admin/user/edit/<int:id>")
def admin_user_edit(id):
    return render_template(
        "admin/user/edit.html",
        module="edit",
        user_id=id
    )


@app.route("/admin/user/delete/<int:id>", methods=["GET", "POST"])
def admin_user_delete(id):
    if request.method == "POST":
        # delete user
        return redirect(url_for("admin_users"))

    return render_template(
        "admin/user/delete.html",
        module="admin",
        user_id=id
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
