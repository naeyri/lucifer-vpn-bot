import telebot
from telebot import types
import requests
import json
import time
import uuid
import os
import io
import qrcode
from flask import Flask

# ==================== تنظیمات عمومی ====================
BOT_TOKEN = "8735674807:AAG3lUzjXyzFLigtXvDrQa1KzX5HDiWfHM4"  # توکن ربات از BotFather
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_IDS = [8738097569, 7384095755]
CARD_NUMBER = "5859831139452311"
CARD_HOLDER = "امید جوادی"

WALLET_FILE = "wallets.json"
FREE_TEST_FILE = "free_tests.json"
USER_SERVICES_FILE = "user_services.json"

def load_json(file_path, is_int_key=False):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if is_int_key:
                    return {int(k): v for k, v in data.items()}
                return data
        except Exception:
            return {}
    return {}

def save_json(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

user_wallets = load_json(WALLET_FILE, is_int_key=True)
free_tested_users = load_json(FREE_TEST_FILE, is_int_key=True)
user_services_db = load_json(USER_SERVICES_FILE, is_int_key=True)

user_orders = {}
deposit_requests = {}

# ==================== تنظیمات پنل پاسارگاد ====================
PANEL_URL = "https://www.speedur.org:2096"
PANEL_USERNAME = "LuciferZzz"
PANEL_PASSWORD = "OMIDLucifer#01"

PLANS = {
    "1": {"name": "۱ گیگابایت", "price_num": 15000, "price": "15,000 تومان", "volume": 1, "days": 30},
    "5": {"name": "۵ گیگابایت", "price_num": 25000, "price": "25,000 تومان", "volume": 5, "days": 30},
    "10": {"name": "۱۰ گیگابایت", "price_num": 50000, "price": "50,000 تومان", "volume": 10, "days": 30},
    "20": {"name": "۲۰ گیگابایت", "price_num": 100000, "price": "100,000 تومان", "volume": 20, "days": 30},
    "30": {"name": "۳۰ گیگابایت", "price_num": 150000, "price": "150,000 تومان", "volume": 30, "days": 30},
    "40": {"name": "۴۰ گیگابایت", "price_num": 200000, "price": "200,000 تومان", "volume": 40, "days": 30},
    "50": {"name": "۵۰ گیگابایت", "price_num": 250000, "price": "250,000 تومان", "volume": 50, "days": 30},
    "unlim": {"name": "۳۰ روزه نامحدود", "price_num": 350000, "price": "350,000 تومان", "volume": 0, "days": 30},
}

def generate_qr_code(text):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = io.BytesIO()
    bio.name = 'qrcode.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

# ==================== تابع ساخت کاربر (کد اصلی و پایدار شما) ====================
def create_panel_client(username, volume_gb, days):
    session = requests.Session()
    requests.packages.urllib3.disable_warnings()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

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
            login_res = session.post(
                f"{PANEL_URL}/api/admin/token",
                json={"username": PANEL_USERNAME, "password": PANEL_PASSWORD},
                timeout=12,
                verify=False
            )
            if login_res.status_code == 200:
                token = login_res.json().get("access_token")
                headers["Authorization"] = f"Bearer {token}"
    except Exception:
        pass

    total_bytes = int(volume_gb * 1024 * 1024 * 1024) if volume_gb > 0 else 0
    expire_timestamp = int(time.time()) + (days * 86400) if days > 0 else 0

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

    try:
        inbound_id = 1
        inbounds_res = session.get(f"{PANEL_URL}/panel/api/inbounds/list", headers=headers, timeout=12, verify=False)
        if inbounds_res.status_code == 200:
            objs = inbounds_res.json().get("obj", [])
            if objs:
                inbound_id = objs[0]["id"]

        client_payload = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [{
                    "id": str(uuid.uuid4()),
                    "email": username,
                    "totalGB": total_bytes,
                    "expiryTime": int(days * 24 * 60 * 60 * 1000),
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
    markup.row(types.KeyboardButton("🛒 خرید سرویس"), types.KeyboardButton("📦 سرویس‌های من"))
    markup.row(types.KeyboardButton("🎁 تست رایگان"), types.KeyboardButton("💼 کیف پول"))
    markup.row(types.KeyboardButton("👥 زیرمجموعه‌گیری"), types.KeyboardButton("📞 پشتیبانی"))
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

def payment_method_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👛 پرداخت از موجودی کیف پول", callback_data="pay_wallet"),
        types.InlineKeyboardButton("💳 کارت به کارت و ارسال رسید", callback_data="pay_card"),
        types.InlineKeyboardButton("❌ انصراف", callback_data="cancel_order")
    )
    return markup

def wallet_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ شارژ کیف پول", callback_data="charge_wallet"))
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
    welcome_text = f"سلام {message.from_user.first_name} عزیز! 🌹\nبه ربات LUCIFER VPN خوش آمدید."
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🎁 تست رایگان")
def free_test_handler(message):
    user_id = message.from_user.id
    if user_id in free_tested_users:
        bot.send_message(message.chat.id, "❌ شما قبلاً از تست رایگان استفاده کرده‌اید.", reply_markup=main_keyboard())
        return

    bot.send_message(message.chat.id, "⏳ در حال ساخت تست ۱ ساعته (۲۵ مگابایت)...")
    test_username = f"test_{user_id}_{int(time.time())}"
    success, result = create_panel_client(username=test_username, volume_gb=0.024414, days=1/24)

    if success:
        free_tested_users[user_id] = True
        save_json(FREE_TEST_FILE, free_tested_users)
        if user_id not in user_services_db:
            user_services_db[user_id] = []
        user_services_db[user_id].append({"username": test_username, "sub_url": result, "type": "تست رایگان"})
        save_json(USER_SERVICES_FILE, user_services_db)
        
        caption_text = f"🎁 **تست رایگان شما ساخته شد!**\n\n⏰ مدت: ۱ ساعت\n📦 حجم: ۲۵ مگابایت\n\n🔑 لینک اشتراک:\n`{result}`"
        bot.send_photo(message.chat.id, generate_qr_code(result), caption=caption_text, reply_markup=main_keyboard(), parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❌ خطا در ساخت تست: {result}", reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "📦 سرویس‌های من")
def my_services_handler(message):
    services = user_services_db.get(message.from_user.id, [])
    if not services:
        bot.send_message(message.chat.id, "📦 هیچ سرویس فعالی یافت نشد.", reply_markup=main_keyboard())
        return
    text = "📦 **سرویس‌های شما:**\n\n"
    for idx, s in enumerate(services, 1):
        text += f"{idx}. `{s['username']}` ({s.get('type', 'معمولی')})\n🔗 `{s['sub_url']}`\n\n"
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "💼 کیف پول")
def show_wallet(message):
    balance = user_wallets.get(message.from_user.id, 0)
    bot.send_message(message.chat.id, f"💼 **کیف پول شما**\n\n💰 موجودی: **{balance:,} تومان**", reply_markup=wallet_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "charge_wallet")
def start_charge_wallet(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "لطفاً مبلغ شارژ را به **تومان** وارد کنید:")
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    try:
        amount = int(message.text.strip())
        if amount < 5000:
            bot.send_message(message.chat.id, "❌ حداقل مبلغ ۵,۰۰۰ تومان است.")
            return
    except ValueError:
        bot.send_message(message.chat.id, "❌ فقط عدد وارد کنید.")
        return
    deposit_requests[message.from_user.id] = {"amount": amount}
    msg = bot.send_message(message.chat.id, f"💳 شماره کارت:\n`{CARD_NUMBER}`\nبه نام: **{CARD_HOLDER}**\n\n📸 عکس رسید واریز را بفرستید.", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_deposit_receipt)

def process_deposit_receipt(message):
    user_id = message.from_user.id
    if not message.photo:
        msg = bot.send_message(message.chat.id, "❌ لطفاً فقط عکس بفرستید.")
        bot.register_next_step_handler(msg, process_deposit_receipt)
        return
    dep_info = deposit_requests.get(user_id)
    if not dep_info:
        return
    bot.send_message(message.chat.id, "✅ رسید دریافت شد. پس از تایید ادمین، حساب شما شارژ می‌شود.", reply_markup=main_keyboard())
    for admin_id in ADMIN_IDS:
        try:
            bot.send_photo(admin_id, message.photo[-1].file_id, caption=f"📥 درخواست شارژ کیف پول\n👤 کاربر: `{user_id}`\n💰 مبلغ: {dep_info['amount']:,} تومان", parse_mode="Markdown")
        except Exception:
            pass

@bot.message_handler(func=lambda msg: msg.text == "👥 زیرمجموعه‌گیری")
def referral_handler(message):
    user_id = message.from_user.id
    ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(message.chat.id, f"👥 **سیستم زیرمجموعه‌گیری**\n\n🔗 لینک دعوت شما:\n`{ref_link}`", reply_markup=main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📞 پشتیبانی")
def support_handler(message):
    bot.send_message(message.chat.id, "📞 برای ارتباط با پشتیبانی به آیدی زیر پیام دهید:\n@Lucifer_ffx", reply_markup=main_keyboard())

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
        f"شما پلن {PLANS[plan_id]['name']} را انتخاب کردید.\n\n"
        f"لطفاً نام کاربری انگلیسی دلخواه ارسال کنید:",
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
        f"🧾 فاکتور سفارش (LUCIFER VPN)\n\n"
        f"📌 نام کاربری: `{username_input}`\n"
        f"📦 سرویس: {selected_plan['name']}\n"
        f"💰 قیمت: {selected_plan['price']}\n\n"
        f"روش پرداخت را انتخاب کنید:"
    )
    bot.send_message(message.chat.id, invoice_text, reply_markup=payment_method_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "pay_wallet")
def pay_via_wallet(call):
    user_id = call.from_user.id
    order = user_orders.get(user_id)
    if not order:
        return
    plan = order["plan"]
    price = plan["price_num"]
    balance = user_wallets.get(user_id, 0)
    if balance < price:
        bot.answer_callback_query(call.id, "❌ موجودی کیف پول کافی نیست.", show_alert=True)
        return

    user_wallets[user_id] -= price
    save_json(WALLET_FILE, user_wallets)
    bot.answer_callback_query(call.id, "در حال ساخت اکانت...")

    success, result = create_panel_client(order["username"], plan["volume"], plan["days"])
    if success:
        if user_id not in user_services_db:
            user_services_db[user_id] = []
        user_services_db[user_id].append({"username": order["username"], "sub_url": result, "type": plan["name"]})
        save_json(USER_SERVICES_FILE, user_services_db)
        
        bot.send_photo(user_id, generate_qr_code(result), caption=f"🎉 خرید موفق با کیف پول!\n\n🔑 لینک اشتراک:\n`{result}`", reply_markup=main_keyboard(), parse_mode="Markdown")
    else:
        user_wallets[user_id] += price
        save_json(WALLET_FILE, user_wallets)
        bot.send_message(user_id, f"❌ خطا در ساخت اکانت: {result}", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "pay_card")
def pay_via_card(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    order = user_orders.get(user_id)
    price = order["plan"]["price"]
    msg = bot.edit_message_text(
        f"💳 شماره کارت:\n`{CARD_NUMBER}`\nبه نام: **{CARD_HOLDER}**\nمبلغ: {price}\n\n📸 لطفاً تصویر رسید پرداخت را ارسال کنید.",
        chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_receipt)

def process_receipt(message):
    user_id = message.from_user.id
    if not message.photo:
        msg = bot.send_message(message.chat.id, "❌ لطفاً فقط عکس رسید را ارسال کنید.")
        bot.register_next_step_handler(msg, process_receipt)
        return

    order_info = user_orders.get(user_id)
    photo_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, "✅ رسید ارسال شد. پس از تایید ادمین، سرویس فعال می‌شود.", reply_markup=main_keyboard())

    admin_caption = (
        f"📥 رسید جدید خرید\n"
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
        if user_id not in user_services_db:
            user_services_db[user_id] = []
        user_services_db[user_id].append({"username": order_info["username"], "sub_url": result, "type": order_info["plan"]["name"]})
        save_json(USER_SERVICES_FILE, user_services_db)

        bot.send_photo(user_id, generate_qr_code(result), caption=f"🎉 پرداخت شما تایید شد!\n\n🔑 لینک اشتراک:\n`{result}`", parse_mode="Markdown")
        bot.edit_message_caption(call.message.caption + f"\n\n✅ تایید شد.\nلینک: `{result}`", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, f"❌ نتیجه ساخت اکانت:\n{result}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_order(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    user_id = int(call.data.replace("reject_", ""))
    bot.send_message(user_id, "❌ پرداخت شما تایید نشد.", reply_markup=main_keyboard())
    bot.edit_message_caption(call.message.caption + "\n\n❌ رد شد.", chat_id=call.message.chat.id, message_id=call.message.message_id)

# ==================== وب‌سرور برای روشن نگه داشتن ربات (مثل Render یا Koyeb) ====================
app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()
    print("🤖 ربات روشن شد...")
    bot.infinity_polling()
    
