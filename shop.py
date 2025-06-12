from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

#
# shop_data = {
#     "Подписки": [
#         ("Discord Nitro", 100, "Месячная подписка на Discord Nitro Full"),
#         ("Spotify Premium", 80, "После покупки вы получите месячную подписку"),
#         ("Годовой Spotify Premium", 300, "После покупки вы получите годовую подписку"),
#         ("Chat GPT+", 280, "После покупки вы получите месячную подписку"),
#         ("Telegram Premium на месяц", 80, "💙 Каждый знает зачем ему нужна эта подписка..."),
#         ("Telegram Premium на год", 300, "💙 Каждый знает зачем ему нужна эта подписка..."),
#     ],
#     "Девайсы": [
#         ("Клавиатура - Ajazz Ak820 (Black)", 420, "После оплаты мы свяжемся с вами"),
#         ("Мышка - VGN R1 SE (Black)", 300, "После оплаты мы свяжемся с вами"),
#     ],
#     "Brawl Stars": [
#         ("Brawl Pass", 180, "После покупки вы получаете боевой пропуск"),
#         ("Brawl Pass +", 250, "После покупки вы получаете боевой пропуск"),
#     ],
#     "Скидка на обучение": [
#         ("Скидка 5000 ₸", 70, "Скидка на следующий месяц обучения"),
#     ],
#     "Косметика": [
#         ("Уникальная роль", 60, "После покупки вы получите кастомную роль"),
#     ],
#     "Мерч": [
#         ("Худи", 400, "После оплаты мы свяжемся с вами"),
#         ("Футболка", 350, "После оплаты мы свяжемся с вами"),
#         ("Кепка", 200, "После оплаты мы свяжемся с вами"),
#     ],
#     "Minecraft": [
#         ("Minecraft Java & Bedrock Edition", 180, "🧡 Аккаунт с лицензионной версией Minecraft"),
#     ]
# }

SHOP_FILE = 'shop_data.json'
def load_shop_data():
    if os.path.exists(SHOP_FILE):
        with open(SHOP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

shop_data = load_shop_data()
def save_shop_data():
    with open(SHOP_FILE, 'w', encoding='utf-8') as f:
        json.dump(shop_data, f, ensure_ascii=False, indent=2)





