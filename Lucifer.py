import telebot
from telebot import types
import requests
import json
import time

# ==================== تنظیمات عمومی ====================
BOT_TOKEN = "8735674807:AAG31UzjXyzFLigtXv"
bot = telebot.TeleBot(BOT_TOKEN)

BOT_USERNAME = "LUC1FER_VPN_BOT"  # آیدی ربات بدون @

ADMIN_IDS = [8738097569, 7384095755]
CARD_NUMBER = "5859831139452311"
CARD_HOLDER = "امید جوادی"

# ==================== تنظیمات پنل ====================
PANEL_URL = "https://www.speedur.org:2096"
PANEL_USERNAME = "LuciferZzz"
PANEL_PASSWORD = "OMIDLucifer#01"

# ==================== لیست قیمت جدید (۳۰ روزه) ====================
PLANS = {
    "1": {"name": "۱ گیگابایت (۳۰ روزه)", "price": 15000},
    "2": {"name": "۵ گیگابایت (۳۰ روزه)", "price": 25000},
    "3": {"name": "۱۰ گیگابایت (۳۰ روزه)", "price": 50000},
    "4": {"name": "۲۰ گیگابایت (۳۰ روزه)", "price": 100000},
    "5": {"name": "۳۰ گیگابایت (۳۰ روزه)", "price": 150000},
    "6": {"name": "۴۰ گیگابایت (۳۰ روزه)", "price": 200000},
    "7": {"name": "۵۰ گیگابایت (۳۰ روزه)", "price": 250000},
    "8": {"name": "نامحدود (۳۰ روزه)", "price": 350000}
}

# ==================== دریافت توکن پنل ====================
def get_panel_token():
    try:
        url = f"{PANEL_URL}/api/admin/token"
        data = {"username": PANEL_USERNAME, "password": PANEL_PASSWORD}
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        print(f"Error getting token: {e}")
    return None

# ==================== ساخت منوی اصلی ====================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_shop = types.KeyboardButton("🛒 خرید سرویس")
    btn_wallet = types.KeyboardButton("👛 کیف پول")
    btn_ref = types.KeyboardButton("👥 زیرمجموعه‌گیری")
    btn_support = types.KeyboardButton("🎧 پشتیبانی")
    
    markup.add(btn_shop, btn_wallet)
    markup.add(btn_ref, btn_support)
    return markup

# ==================== دستور /start ====================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_first_name = message.from_user.first_name
    welcome_text = (
        f"سلام {user_first_name} عزیز! 👋\n"
        "به ربات لوسیفر خوش آمدید. لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

# ==================== مدیریت دکمه‌های منو ====================
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    text = message.text

    # ۱. خرید سرویس
    if text == "🛒 خرید سرویس":
        markup = types.InlineKeyboardMarkup(row_width=1)
        for plan_id, plan_info in PLANS.items():
            btn = types.InlineKeyboardButton(
                f"🔹 {plan_info['name']} - {plan_info['price']:,} تومان", 
                callback_data=f"buy_{plan_id}"
            )
            markup.add(btn)
        bot.send_message(message.chat.id, "لطفاً پلن مورد نظر خود را برای خرید انتخاب کنید:", reply_markup=markup)

    # ۲. کیف پول
    elif text == "👛 کیف پول":
        wallet_text = (
            "💳 **بخش کیف پول**\n\n"
            "💰 موجودی حساب شما: **۰ تومان**\n\n"
            f"شماره کارت جهت شارژ:\n`{CARD_NUMBER}`\nبه نام: {CARD_HOLDER}\n\n"
            "پس از واریز، فیش را برای پشتیبانی ارسال کنید."
        )
        bot.send_message(message.chat.id, wallet_text, parse_mode="Markdown")

    # ۳. زیرمجموعه‌گیری
    elif text == "👥 زیرمجموعه‌گیری":
        user_id = message.from_user.id
        ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        ref_text = (
            "🎁 **بخش زیرمجموعه‌گیری**\n\n"
            "با دعوت دوستان خود از طریق لینک زیر هدیه بگیرید:\n\n"
            f"🔗 لینک اختصاصی شما:\n`{ref_link}`"
        )
        bot.send_message(message.chat.id, ref_text, parse_mode="Markdown")

    # ۴. پشتیبانی
    elif text == "🎧 پشتیبانی":
        support_text = (
            "🎧 **بخش پشتیبانی**\n\n"
            "برای ارتباط با مدیریت و پشتیبانی آنلاین، پیام دهید:\n\n"
            "👤 پشتیبانی اول: @Lucifer_ffx\n"
            "👤 پشتیبانی دوم: @naeyri1"
        )
        bot.send_message(message.chat.id, support_text, parse_mode="Markdown")

# ==================== اجرای ربات ====================
print("🤖 ربات با پلن‌های جدید ۳۰ روزه روشن شد...")
bot.infinity_polling()
