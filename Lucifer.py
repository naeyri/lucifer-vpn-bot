import telebot
from telebot import types

# توکن رباتت
TOKEN = "8735674807:AAG3lUzjXyzFLigtXvDrQa1KzX5HDiWfHM4"
bot = telebot.TeleBot(TOKEN)

# ==================== منوی اصلی ====================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_shop = types.KeyboardButton("🛒 خرید سرویس")
    btn_wallet = types.KeyboardButton("👛 کیف پول")
    btn_ref = types.KeyboardButton("👥 زیرمجموعه‌گیری")
    btn_support = types.KeyboardButton("🎧 پشتیبانی")
    
    markup.add(btn_shop, btn_wallet)
    markup.add(btn_ref, btn_support)
    return markup

# ==================== دستور START ====================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_first_name = message.from_user.first_name
    welcome_text = f"سلام {user_first_name} عزیز! 👋\nبه ربات خوش آمدید. لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

# ==================== مدیریت دکمه‌های متنی ====================
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    text = message.text

    # 1. خرید سرویس
    if text == "🛒 خرید سرویس":
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("پلن ۱ ماهه - ۵۰ گیگ", callback_data="buy_1m")
        markup.add(btn1)
        bot.send_message(message.chat.id, "لطفاً پلن مورد نظر خود را انتخاب کنید:", reply_markup=markup)

    # 2. کیف پول
    elif text == "👛 کیف پول":
        wallet_text = (
            "💳 **بخش کیف پول**\n\n"
            "💰 موجودی شما: ۰ تومان\n\n"
            "جهت شارژ حساب با پشتیبانی در ارتباط باشید."
        )
        bot.send_message(message.chat.id, wallet_text, parse_mode="Markdown")

    # 3. زیرمجموعه‌گیری
    elif text == "👥 زیرمجموعه‌گیری":
        user_id = message.from_user.id
        ref_link = f"https://t.me/اسم_ربات_شما?start={user_id}"
        ref_text = (
            "🎁 **بخش زیرمجموعه‌گیری**\n\n"
            "با دعوت دوستان خود، هدیه بگیرید!\n"
            f"🔗 لینک اختصاصی شما:\n`{ref_link}`"
        )
        bot.send_message(message.chat.id, ref_text, parse_mode="Markdown")

    # 4. پشتیبانی
    elif text == "🎧 پشتیبانی":
        support_text = (
            "📞 **بخش پشتیبانی**\n\n"
            "برای ارتباط با آیدی زیر در تماس باشید:\n"
            "🆔 @LuciferZzz"
        )
        bot.send_message(message.chat.id, support_text, parse_mode="Markdown")

# ==================== اجرای ربات ====================
print("🤖 ربات با موفقیت روشن شد...")
bot.infinity_polling()
