import telebot
from telebot import types
import requests
import json
import time
import uuid
import os
from flask import Flask

# ==================== تنظیمات عمومی ====================
BOT_TOKEN = "8735674807:AAG3lUzjXyzFLigtXvDrQa1KzX5HDiWfHM4"
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_IDS = [8738097569, 7384095755]
CARD_NUMBER = "5859831139452311"
CARD_HOLDER = "امید جوادی"

# ==================== مدیریت دائمی کیف پول ====================
WALLET_FILE = "wallets.json"

def load_wallets():
    if os.path.exists(WALLET_FILE):
        try:
            with open(WALLET_FILE, "r", encoding="utf-8") as f:
                # تبدیل کلیدها به عدد صحیح (چونکه جیسون کلیدها رو استرینگ ذخیره میکنه)
                return {int(k): v for k, v in json.load(f).items()}
        except Exception:
            return {}
    return {}

def save_wallets():
    try:
        with open(WALLET_FILE, "w", encoding="utf-8") as f:
            json.dump(user_wallets, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"خطا در ذخیره کیف پول: {e}")

user_wallets = load_wallets()
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

# ==================== تابع ساخت کاربر در پنل پاسارگاد ====================
def create_panel_client(username, volume_gb, days):
    session = requests.Session()
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

    total_bytes = volume_gb * 1024 * 1024 * 1024 if volume_gb > 0 else 0
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
    markup.row(types.KeyboardButton("💼 کیف پول"), types.KeyboardButton("📞 پشتیبانی"))
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

def admin_deposit_keyboard(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ تایید شارژ حساب", callback_data=f"depapprove_{user_id}"),
        types.InlineKeyboardButton("❌ رد شارژ", callback_data=f"depreject_{user_id}")
    )
    return markup

# ==================== هندلرها ====================

@bot.message_handler(commands=['start'])
def start_handler(message):
    welcome_text = f"سلام {message.from_user.first_name} عزیز! 🌹\nبه ربات LUCIFER VPN خوش آمدید."
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "💼 کیف پول")
def show_wallet(message):
    user_id = message.from_user.id
    balance = user_wallets.get(user_id, 0)
    wallet_text = (
        f"💼 **کیف پول شما**\n\n"
        f"💰 موجودی فعلی: **{balance:,} تومان**\n\n"
        f"با شارژ کیف پول می‌توانید تمام خریدهای خود را به‌صورت آنی انجام دهید."
    )
    bot.send_message(message.chat.id, wallet_text, reply_markup=wallet_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "charge_wallet")
def start_charge_wallet(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "لطفاً مبلغ مورد نظر جهت شارژ را به **تومان** وارد کنید:\n(مثلاً: 50000)")
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    try:
        amount = int(message.text.strip())
        if amount < 5000:
            bot.send_message(message.chat.id, "❌ حداقل مبلغ شارژ ۵,۰۰۰ تومان می‌باشد.")
            return
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً مبلغ را فقط به صورت عدد وارد کنید.")
        return

    user_id = message.from_user.id
    deposit_requests[user_id] = {"amount": amount}

    charge_text = (
        f"📌 **درخواست شارژ حساب**\n\n"
        f"💵 مبلغ: **{amount:,} تومان**\n\n"
        f"💳 شماره کارت جهت واریز:\n`{CARD_NUMBER}`\nبه نام: **{CARD_HOLDER}**\n\n"
        f"📸 لطفاً پس از واریز، تصویر رسید پرداخت را ارسال کنید."
    )
    msg = bot.send_message(message.chat.id, charge_text, parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_deposit_receipt)

def process_deposit_receipt(message):
    user_id = message.from_user.id
    if not message.photo:
        msg = bot.send_message(message.chat.id, "❌ لطفاً فقط عکس رسید را ارسال کنید.")
        bot.register_next_step_handler(msg, process_deposit_receipt)
        return

    dep_info = deposit_requests.get(user_id)
    if not dep_info:
        return

    photo_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, "✅ رسید شارژ دریافت شد. پس از بررسی ادمین، کیف پول شما شارژ می‌شود.")

    admin_caption = (
        f"📥 **درخواست شارژ کیف پول**\n"
        f"👤 کاربر: {message.from_user.first_name}\n"
        f"🆔 آیدی عددی: `{user_id}`\n"
        f"💰 مبلغ درخواست: **{dep_info['amount']:,} تومان**"
    )

    for admin_id in ADMIN_IDS:
        try:
            bot.send_photo(admin_id, photo_id, caption=admin_caption, reply_markup=admin_deposit_keyboard(user_id), parse_mode="Markdown")
        except Exception as e:
            print(f"خطا در ارسال به ادمین: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("depapprove_"))
def approve_deposit(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    user_id = int(call.data.replace("depapprove_", ""))
    dep_info = deposit_requests.get(user_id)

    if not dep_info:
        bot.answer_callback_query(call.id, "اطلاعات درخواست یافت نشد.", show_alert=True)
        return

    amount = dep_info["amount"]
    user_wallets[user_id] = user_wallets.get(user_id, 0) + amount
    save_wallets()  # ذخیره در فایل

    bot.send_message(user_id, f"🎉 کیف پول شما با موفقیت مبلغ **{amount:,} تومان** شارژ شد!\n💰 موجودی جدید: **{user_wallets[user_id]:,} تومان**", parse_mode="Markdown")
    bot.edit_message_caption(call.message.caption + f"\n\n✅ **شارژ تایید شد.**", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
    bot.answer_callback_query(call.id, "شارژ تایید شد.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("depreject_"))
def reject_deposit(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    user_id = int(call.data.replace("depreject_", ""))
    bot.send_message(user_id, "❌ رسید شارژ کیف پول شما مورد تایید قرار نگرفت.")
    bot.edit_message_caption(call.message.caption + "\n\n❌ **شارژ رد شد.**", chat_id=call.message.chat.id, message_id=call.message.message_id)

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
        f"لطفاً نام کاربری انگلیسی دلخواه برای ساخت کانکشن ارسال کنید:",
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
    balance = user_wallets.get(user_id, 0)

    invoice_text = (
        f"🧾 **فاکتور سفارش (LUCIFER VPN)**\n\n"
        f"📌 نام کاربری: `{username_input}`\n"
        f"📦 سرویس: **{selected_plan['name']}**\n"
        f"💰 قیمت: **{selected_plan['price']}**\n\n"
        f"💰 موجودی کیف پول شما: **{balance:,} تومان**\n\n"
        f"لطفاً روش پرداخت را انتخاب کنید:"
    )
    bot.send_message(message.chat.id, invoice_text, reply_markup=payment_method_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "pay_wallet")
def pay_via_wallet(call):
    user_id = call.from_user.id
    order_info = user_orders.get(user_id)

    if not order_info:
        bot.answer_callback_query(call.id, "سفارش یافت نشد.", show_alert=True)
        return

    price = order_info["plan"]["price_num"]
    balance = user_wallets.get(user_id, 0)

    if balance < price:
        bot.answer_callback_query(call.id, "❌ موجودی کیف پول کافی نیست.", show_alert=True)
        return

    user_wallets[user_id] -= price
    save_wallets()  # ذخیره در فایل
    bot.answer_callback_query(call.id, "در حال ساخت سرویس...")

    bot.edit_message_text("⚡️ مبلغ کسر شد. در حال ساخت کانکشن...", chat_id=call.message.chat.id, message_id=call.message.message_id)

    success, result = create_panel_client(
        username=order_info["username"],
        volume_gb=order_info["plan"]["volume"],
        days=order_info["plan"]["days"]
    )

    if success:
        user_msg = f"🎉 **خرید با موفقیت انجام شد!**\n\n🔑 لینک کانکشن شما:\n`{result}`"
        bot.send_message(user_id, user_msg, parse_mode="Markdown")
    else:
        user_wallets[user_id] += price
        save_wallets()  # ذخیره در فایل در صورت خطا و برگشت پول
        bot.send_message(user_id, f"❌ خطا در ساخت اکانت. مبلغ بازگردانده شد.\nعلت: {result}")

@bot.callback_query_handler(func=lambda call: call.data == "pay_card")
def pay_via_card(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    order_info = user_orders.get(user_id)

    card_text = (
        f"💳 **پرداخت مستقیم**\n\n"
        f"شماره کارت:\n`{CARD_NUMBER}`\nبه نام: **{CARD_HOLDER}**\n\n"
        f"مبلغ قابل پرداخت: **{order_info['plan']['price']}**\n\n"
        f"📸 لطفاً تصویر رسید واریز را ارسال کنید."
    )
    msg = bot.edit_message_text(card_text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_receipt)

def process_receipt(message):
    user_id = message.from_user.id
    if not message.photo:
        msg = bot.send_message(message.chat.id, "❌ لطفاً فقط عکس رسید را ارسال کنید.")
        bot.register_next_step_handler(msg, process_receipt)
        return

    order_info = user_orders.get(user_id)
    photo_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, "✅ رسید ارسال شد. پس از تایید ادمین، سرویس فعال می‌شود.")

    admin_caption = (
        f"📥 **رسید خرید جدید**\n"
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
        user_msg = f"🎉 پرداخت شما تایید شد!\n\n🔑 لینک کانکشن شما:\n`{result}`"
        bot.send_message(user_id, user_msg, parse_mode="Markdown")
        bot.edit_message_caption(call.message.caption + f"\n\n✅ **تایید شد.**\nلینک: `{result}`", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, f"❌ نتیجه ساخت اکانت:\n{result}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_order(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    user_id = int(call.data.replace("reject_", ""))
    bot.send_message(user_id, "❌ پرداخت شما تایید نشد.")
    bot.edit_message_caption(call.message.caption + "\n\n❌ **رد شد.**", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.message_handler(func=lambda msg: msg.text == "📞 پشتیبانی")
def support_handler(message):
    support_text = (
        "🎧 **بخش پشتیبانی ربات لوسیفر**\n\n"
        "برای پاسخگویی به سوالات، مشاوره یا رفع مشکلات با آیدی‌های زیر در تماس باشید:\n\n"
        "👤 پشتیبانی اول: @Lucifer_ffx\n"
        "👤 پشتیبانی دوم: @naeyri1"
    )
    bot.send_message(message.chat.id, support_text, parse_mode="Markdown")

# ==================== وب‌سرور فیک برای رندر ====================
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    import threading
    t = threading.Thread(target=run_web)
    t.start()
    
    print("🤖 ربات روشن شد...")
    bot.infinity_polling()
    
