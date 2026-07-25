import telebot
from telebot import types
import requests
import json
import time

# ==================== تنظیمات عمومی ====================
BOT_TOKEN = "8735674807:AAG3lUzjXyzFLigtXvDrQa1KzX5HDiWfHM4"  # توکن ربات از BotFather
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_IDS = [8738097569, 7384095755]
CARD_NUMBER = "5859831139452311"
CARD_HOLDER = "امید جوادی"

# ==================== تنظیمات پنل پاسارگاد ====================
PANEL_URL = "https://www.speedur.org:2096"
PANEL_USERNAME = "LuciferZzz"
PANEL_PASSWORD = "OMIDLucifer#01"

PLANS = {
    "1": {"name": "۱ گیگابایت", "price": "15,000 تومان", "volume": 1, "days": 30},
    "5": {"name": "۵ گیگابایت", "price": "25,000 تومان", "volume": 5, "days": 30},
    "10": {"name": "۱۰ گیگابایت", "price": "50,000 تومان", "volume": 10, "days": 30},
    "20": {"name": "۲۰ گیگابایت", "price": "100,000 تومان", "volume": 20, "days": 30},
    "30": {"name": "۳۰ گیگابایت", "price": "150,000 تومان", "volume": 30, "days": 30},
    "40": {"name": "۴۰ گیگابایت", "price": "200,000 تومان", "volume": 40, "days": 30},
    "50": {"name": "۵۰ گیگابایت", "price": "250,000 تومان", "volume": 50, "days": 30},
    "unlim": {"name": "۳۰ روزه نامحدود", "price": "350,000 تومان", "volume": 0, "days": 30},
}

user_orders = {}

# ==================== تابع هوشمند ساخت کاربر پاسارگاد ====================
def create_panel_client(username, volume_gb, days):
    session = requests.Session()
    requests.packages.urllib3.disable_warnings()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # ۱. دریافت توکن لاگین پاسارگاد
    token = None
    try:
        login_res = session.post(
            f"{PANEL_URL}/api/admin/token",
            data={"username": PANEL_USERNAME, "password": PANEL_PASSWORD},
            timeout=12,
            verify=False
        )
        if login_res.status_code == 200:
            token = login_res.json().get("access_token")
            headers["Authorization"] = f"Bearer {token}"
        else:
            # تست مسیر لاگین JSON
            login_res = session.post(
                f"{PANEL_URL}/api/admin/token",
                json={"username": PANEL_USERNAME, "password": PANEL_PASSWORD},
                timeout=12,
                verify=False
            )
            if login_res.status_code == 200:
                token = login_res.json().get("access_token")
                headers["Authorization"] = f"Bearer {token}"
    except Exception as e:
        pass

    # محاسبه حجم و انقضا
    total_bytes = volume_gb * 1024 * 1024 * 1024 if volume_gb > 0 else 0
    expire_timestamp = int(time.time()) + (days * 86400) if days > 0 else 0

    # ۲. ساخت کاربر در سیستم پاسارگاد (روش مستقیم Native API)
    pasarguad_payload = {
        "username": username,
        "data_limit": total_bytes,
        "expire": expire_timestamp,
        "status": "active",
        "proxies": {"vless": {}},
        "inbounds": {}
    }

    try:
        user_res = session.post(f"{PANEL_URL}/api/user", json=pasarguad_payload, headers=headers, timeout=12, verify=False)
        if user_res.status_code in [200, 201]:
            user_data = user_res.json()
            sub_url = user_data.get("subscription_url", f"{PANEL_URL}/sub/{username}")
            return True, sub_url
    except Exception:
        pass

    # ۳. روش جایگزین (اگر روش ۱ جواب نداد - سیستم 3x-ui / v2-ui)
    try:
        inbound_id = 1
        inbounds_res = session.get(f"{PANEL_URL}/panel/api/inbounds/list", headers=headers, timeout=12, verify=False)
        if inbounds_res.status_code == 200:
            objs = inbounds_res.json().get("obj", [])
            if objs:
                inbound_id = objs[0]["id"]

        import uuid
        client_payload = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [{
                    "id": str(uuid.uuid4()),
                    "email": username,
                    "totalGB": total_bytes,
                    "expiryTime": days * 24 * 60 * 60 * 1000,
                    "enable": True
                }]
            })
        }
        add_res = session.post(f"{PANEL_URL}/panel/api/inbounds/addClient", json=client_payload, headers=headers, timeout=12, verify=False)
        res_json = add_res.json()
        if res_json.get("success"):
            return True, f"{PANEL_URL}/sub/{username}"
        else:
            return False, f"پاسخ پنل: {res_json.get('msg', add_res.text)}"
    except Exception as e:
        return False, f"خطای ساخت اکانت: {str(e)}"

# ==================== کیبوردها ====================
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🛒 خرید سرویس"))
    markup.row(types.KeyboardButton("💼 کیف پول"), types.KeyboardButton("👥 زیرمجموعه‌گیری"))
    markup.row(types.KeyboardButton("📞 پشتیبانی"))
    return markup

def plans_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for plan_id, plan_info in PLANS.items():
        text = f"{plan_info['name']} - {plan_info['price']}"
        buttons.append(types.InlineKeyboardButton(text=text, callback_data=f"buy_{plan_id}"))
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("❌ انصراف", callback_data="cancel_order"))
    return markup

def admin_receipt_keyboard(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ تایید و ساخت کانکشن", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{user_id}")
    )
    return markup

# ==================== هندلرها ====================
@bot.message_handler(commands=['start'])
def start_handler(message):
    welcome_text = f"سلام {message.from_user.first_name} عزیز! 🌹\nبه ربات **LUCIFER VPN** خوش آمدید."
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🛒 خرید سرویس")
def show_plans(message):
    bot.send_message(message.chat.id, "لطفاً پلن مورد نظر خودت رو انتخاب کن:", reply_markup=plans_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "cancel_order")
def cancel_order(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text("سفارش شما لغو شد.", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def select_plan(call):
    plan_id = call.data.replace("buy_", "")
    if plan_id not in PLANS:
        return
    bot.answer_callback_query(call.id)
    user_orders[call.from_user.id] = {"plan": PLANS[plan_id]}

    msg = bot.edit_message_text(
        f"شما پلن **{PLANS[plan_id]['name']}** را انتخاب کردید.\n\n"
        f"لطفاً **نام کاربری انگلیسی** دلخواه ارسال کنید:",
        chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_username)

def process_username(message):
    user_id = message.from_user.id
    if user_id not in user_orders:
        return
    username_input = message.text.strip().replace(" ", "_")
    user_orders[user_id]["username"] = username_input
    selected_plan = user_orders[user_id]["plan"]

    invoice_text = (
        f"🧾 **فاکتور سفارش (LUCIFER VPN)**\n\n"
        f"📌 **نام کاربری:** `{username_input}`\n"
        f"📦 **سرویس:** {selected_plan['name']}\n"
        f"💰 **قیمت:** {selected_plan['price']}\n\n"
        f"💳 **شماره کارت:** `{CARD_NUMBER}` ({CARD_HOLDER})\n\n"
        f"📸 **لطفاً تصویر رسید پرداخت را ارسال کنید.**"
    )
    msg = bot.send_message(message.chat.id, invoice_text, parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_receipt)

def process_receipt(message):
    user_id = message.from_user.id
    if not message.photo:
        msg = bot.send_message(message.chat.id, "❌ لطفاً فقط **عکس رسید** را ارسال کنید.")
        bot.register_next_step_handler(msg, process_receipt)
        return

    order_info = user_orders.get(user_id)
    photo_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, "✅ رسید ارسال شد. پس از تایید، سرویس فعال می‌شود.")

    admin_caption = (
        f"📥 **رسید جدید**\n"
        f"👤 کاربر: {message.from_user.first_name}\n"
        f"🆔 آیدی عددی: `{user_id}`\n"
        f"📦 سرویس: {order_info['plan']['name']}\n"
        f"🔑 نام کاربری: `{order_info['username']}`"
    )

    for admin_id in ADMIN_IDS:
        try:
            bot.send_photo(admin_id, photo_id, caption=admin_caption, reply_markup=admin_receipt_keyboard(user_id), parse_mode="Markdown")
        except Exception as e:
            print(f"خطا در ارسال به ادمین: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_order(call):
    if call.from_user.id not in ADMIN_IDS:
        return

    user_id = int(call.data.replace("approve_", ""))
    order_info = user_orders.get(user_id)

    if not order_info:
        bot.answer_callback_query(call.id, "اطلاعات سفارش یافت نشد.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "در حال ساخت اکانت...")

    success, result = create_panel_client(
        username=order_info["username"],
        volume_gb=order_info["plan"]["volume"],
        days=order_info["plan"]["days"]
    )

    if success:
        user_msg = f"🎉 **پرداخت تایید شد!**\n\n🔑 **لینک کانکشن شما:**\n`{result}`"
        bot.send_message(user_id, user_msg, parse_mode="Markdown")
        bot.edit_message_caption(call.message.caption + f"\n\n✅ **تایید شد.**\nلینک: `{result}`", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, f"❌ **نتیجه ساخت اکانت:**\n{result}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_order(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    user_id = int(call.data.replace("reject_", ""))
    bot.send_message(user_id, "❌ **پرداخت شما تایید نشد.**")
    bot.edit_message_caption(call.message.caption + "\n\n❌ **رد شد.**", chat_id=call.message.chat.id, message_id=call.message.message_id)

print("🤖 ربات روشن شد...")
bot.infinity_polling()
          
