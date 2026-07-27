import telebot
from telebot import types
import requests
import json
import os
import time
from flask import Flask
import threading
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()

BOT_TOKEN = "8735674807:AAG3lUzjXyzFLigtXvDrQa1KzX5HDiWfHM4"
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_IDS = [8738097569, 7384095755]
CARD_NUMBER = "5859831139452311"
CARD_HOLDER = "امید جوادی"

WALLETS_FILE = "wallets.json"
FREE_TEST_FILE = "free_tested.json"
REFERRALS_FILE = "referrals.json"
SERVICES_FILE = "user_services.json"

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

user_wallets = load_json(WALLETS_FILE)
free_tested_users = load_json(FREE_TEST_FILE)
referral_data = load_json(REFERRALS_FILE)
user_services_db = load_json(SERVICES_FILE)

PANEL_URL = "https://www.speedur.org:2096"
PANEL_USERNAME = "LuciferZzz"
PANEL_PASSWORD = "OMIDLucifer#01"

PLANS = {
    "1": {"name": "۱ گیگابایت", "price": "15,000 تومان", "price_num": 15000, "volume": 1, "days": 30},
    "5": {"name": "۵ گیگابایت", "price": "25,000 تومان", "price_num": 25000, "volume": 5, "days": 30},
    "10": {"name": "۱۰ گیگابایت", "price": "50,000 تومان", "price_num": 50000, "volume": 10, "days": 30},
    "20": {"name": "۲۰ گیگابایت", "price": "100,000 تومان", "price_num": 100000, "volume": 20, "days": 30},
    "30": {"name": "۳۰ گیگابایت", "price": "150,000 تومان", "price_num": 150000, "volume": 30, "days": 30},
    "40": {"name": "۴۰ گیگابایت", "price": "200,000 تومان", "price_num": 200000, "volume": 40, "days": 30},
    "50": {"name": "۵۰ گیگابایت", "price": "250,000 تومان", "price_num": 250000, "volume": 50, "days": 30},
    "unlim": {"name": "۳۰ روزه نامحدود", "price": "350,000 تومان", "price_num": 350000, "volume": 0, "days": 30},
}

user_orders = {}
deposit_requests = {}

def get_marzban_token():
    url = f"{PANEL_URL}/api/admin/token"
    data = {
        "username": PANEL_USERNAME,
        "password": PANEL_PASSWORD
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "accept": "application/json"
    }
    try:
        response = requests.post(url, data=data, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        print(f"Token Error: {e}")
    return None

def create_panel_client(username, volume_gb, days):
    token = get_marzban_token()
    if not token:
        return False, "خطا در احراز هویت با پنل (توکن دریافت نشد)."

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    
    expire_timestamp = int(time.time()) + (days * 86400) if days > 0 else None
    total_bytes = int(volume_gb * 1024 * 1024 * 1024) if volume_gb > 0 else 0

    payload = {
        "username": username,
        "proxies": {
            "vless": {},
            "vmess": {},
            "trojan": {}
        },
        "inbounds": {
            "vless": ["VLESS + TLS", "VLESS TCP"],
            "vmess": ["VMess TCP"],
            "trojan": ["Trojan TCP"]
        },
        "expire": expire_timestamp,
        "data_limit": total_bytes,
        "data_limit_reset_strategy": "no_reset"
    }

    endpoints = [
        f"{PANEL_URL}/api/user",
        f"{PANEL_URL}/api/users"
    ]

    last_error = ""
    for url in endpoints:
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15, verify=False)
            if response.status_code in [200, 201]:
                user_data = response.json()
                sub_url = user_data.get("subscription_url") or f"{PANEL_URL}/sub/{username}"
                return True, sub_url
            else:
                last_error = f"کد خطا {response.status_code}: {response.text}"
        except Exception as e:
            last_error = str(e)

    return False, last_error

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🛒 خرید سرویس"), types.KeyboardButton("🎁 تست رایگان"))
    markup.row(types.KeyboardButton("📦 سرویس‌های من"), types.KeyboardButton("💼 کیف پول"))
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

def support_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🛠 پشتیبانی VPN", url="https://t.me/LUCIFER_FFX"),
        types.InlineKeyboardButton("🤖 پشتیبانی ربات", url="https://t.me/naeyri1")
    )
    return markup

def payment_method_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👛 پرداخت از کیف پول", callback_data="pay_wallet"),
        types.InlineKeyboardButton("💳 کارت به کارت", callback_data="pay_card"),
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

def admin_deposit_keyboard(user_id, amount):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ تایید و شارژ", callback_data=f"depapp_{user_id}_{amount}"),
        types.InlineKeyboardButton("❌ رد", callback_data=f"deprej_{user_id}")
    )
    return markup

def user_services_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    u_services = user_services_db.get(str(user_id), [])
    for idx, s in enumerate(u_services):
        markup.add(types.InlineKeyboardButton(f"📌 {s['username']} ({s['plan_name']})", callback_data=f"myserv_{idx}"))
    markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
    return markup

def single_service_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔄 تمدید سرویس", callback_data="renew_service"),
        types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_services")
    )
    return markup
    @bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
            if referrer_id != user_id:
                if str(referrer_id) not in referral_data:
                    referral_data[str(referrer_id)] = []
                if user_id not in referral_data[str(referrer_id)]:
                    referral_data[str(referrer_id)].append(user_id)
                    save_json(REFERRALS_FILE, referral_data)
                    
                    current_bal = user_wallets.get(str(referrer_id), 0)
                    user_wallets[str(referrer_id)] = current_bal + 5000
                    save_json(WALLETS_FILE, user_wallets)
                    try:
                        bot.send_message(referrer_id, "🎉 یک زیرمجموعه جدید ثبت شد! مبلغ ۵,۰۰۰ تومان به کیف پولت اضافه شد.")
                    except:
                        pass
        except:
            pass

    welcome_text = "به دنیای ارتباط امن و پرسرعت **LUCIFER VPN** خوش آمدید! 🚀⚡️\n\nبا استفاده از منوی زیر می‌توانید سرویس خود را خریداری کنید، تست رایگان بگیرید یا از امکانات کیف پول و پشتیبانی بهره‌مند شوید 👇"
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🛒 خرید سرویس")
def show_plans(message):
    bot.send_message(message.chat.id, "لطفاً پلن مورد نظر خودت رو انتخاب کن:", reply_markup=plans_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "🎁 تست رایگان")
def free_test_handler(message):
    user_id = message.from_user.id
    if str(user_id) in free_tested_users or user_id in free_tested_users:
        bot.send_message(message.chat.id, "❌ شما قبلاً از تست رایگان استفاده کرده‌اید و امکان دریافت مجدد آن را ندارید.", reply_markup=main_keyboard())
        return

    bot.send_message(message.chat.id, "⏳ در حال ساخت تست رایگان (۲۵ مگابایت - ۱ ساعته)...")
    test_username = f"test_{user_id}_{int(time.time())}"
    
    success, result = create_panel_client(username=test_username, volume_gb=0.0244, days=1)

    if success:
        free_tested_users[str(user_id)] = True
        save_json(FREE_TEST_FILE, free_tested_users)
        
        if str(user_id) not in user_services_db:
            user_services_db[str(user_id)] = []
        user_services_db[str(user_id)].append({
            "username": test_username,
            "plan_name": "تست رایگان",
            "sub_url": result,
            "volume": 0.0244,
            "days": 1
        })
        save_json(SERVICES_FILE, user_services_db)
        
        test_msg = (
            f"🎁 **تست رایگان شما با موفقیت ساخته شد!**\n\n"
            f"👤 نام کاربری: `{test_username}`\n"
            f"⏰ مدت اعتبار: ۱ ساعت (۲۵ مگابایت)\n\n"
            f"🔑 لینک اشتراک (ساب):\n`{result}`"
        )
        bot.send_message(message.chat.id, test_msg, reply_markup=main_keyboard(), parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❌ خطا در ساخت تست رایگان:\n{result}", reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "📦 سرویس‌های من")
def show_user_services(message):
    user_id = str(message.from_user.id)
    u_services = user_services_db.get(user_id, [])
    if not u_services:
        bot.send_message(message.chat.id, "❌ شما هیچ سرویس فعالی ندارید.", reply_markup=main_keyboard())
        return
    bot.send_message(message.chat.id, "📦 سرویس‌های فعال شما:", reply_markup=user_services_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("myserv_"))
def show_single_service(call):
    user_id = str(call.from_user.id)
    idx = int(call.data.split("_")[1])
    u_services = user_services_db.get(user_id, [])
    if idx >= len(u_services):
        bot.answer_callback_query(call.id, "سرویس یافت نشد.", show_alert=True)
        return
    
    service = u_services[idx]
    user_orders[call.from_user.id] = {"selected_service_index": idx, "username": service["username"]}
    
    text = (
        f"📌 جزئیات سرویس:\n\n"
        f"👤 نام کاربری: `{service['username']}`\n"
        f"📦 پلن: {service['plan_name']}\n\n"
        f"🔑 لینک اشتراک (ساب):\n`{service['sub_url']}`"
    )
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=single_service_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_services")
def back_to_services(call):
    user_id = str(call.from_user.id)
    bot.edit_message_text("📦 سرویس‌های فعال شما:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=user_services_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "منوی اصلی:", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "renew_service")
def renew_service_menu(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text("لطفاً پلن تمدید مورد نظر خود را انتخاب کنید:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=plans_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "💼 کیف پول")
def show_wallet(message):
    user_id = str(message.from_user.id)
    balance = user_wallets.get(user_id, 0)
    bot.send_message(message.chat.id, f"💼 **کیف پول شما**\n\n💰 موجودی فعلی: **{balance:,} تومان**", reply_markup=wallet_keyboard(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "charge_wallet")
def start_charge_wallet(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "لطفاً مبلغ شارژ مورد نظر را به **تومان** وارد کنید:")
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    try:
        amount = int(message.text.strip())
        if amount < 5000:
            bot.send_message(message.chat.id, "❌ حداقل مبلغ شارژ ۵,۰۰۰ تومان است.")
            return
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً فقط عدد وارد کنید.")
        return
    
    deposit_requests[message.from_user.id] = {"amount": amount}
    msg = bot.send_message(
        message.chat.id,
        f"💳 شماره کارت جهت واریز:\n`{CARD_NUMBER}`\nبه نام: **{CARD_HOLDER}**\nمبلغ: {amount:,} تومان\n\n📸 لطفاً تصویر رسید واریز را بفرستید.",
        parse_mode="Markdown"
    )
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
    amount = dep_info["amount"]
    photo_id = message.photo[-1].file_id
    
    bot.send_message(message.chat.id, "✅ رسید شما دریافت شد. پس از تایید ادمین، حساب شما شارژ می‌شود.", reply_markup=main_keyboard())

    for admin_id in ADMIN_IDS:
        try:
            bot.send_photo(
                admin_id, photo_id,
                caption=f"📥 درخواست شارژ کیف پول\n👤 کاربر: `{user_id}`\n💰 مبلغ: {amount:,} تومان",
                reply_markup=admin_deposit_keyboard(user_id, amount),
                parse_mode="Markdown"
            )
        except:
            pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("depapp_"))
def approve_deposit(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    parts = call.data.split("_")
    user_id = int(parts[1])
    amount = int(parts[2])
    
    current_bal = user_wallets.get(str(user_id), 0)
    user_wallets[str(user_id)] = current_bal + amount
    save_json(WALLETS_FILE, user_wallets)
    
    bot.answer_callback_query(call.id, "کیف پول کاربر شارژ شد.")
    bot.send_message(user_id, f"🎉 پرداخت شما تایید شد!\n💰 مبلغ {amount:,} تومان به کیف پول شما اضافه شد.", reply_markup=main_keyboard())
    bot.edit_message_caption(call.message.caption + f"\n\n✅ تایید شد و {amount:,} تومان واریز گردید.", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deprej_"))
def reject_deposit(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    user_id = int(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "درخواست رد شد.")
    bot.send_message(user_id, "❌ رسید شارژ کیف پول شما تایید نشد.", reply_markup=main_keyboard())
    bot.edit_message_caption(call.message.caption + "\n\n❌ رد شد.", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.message_handler(func=lambda msg: msg.text == "👥 زیرمجموعه‌گیری")
def referral_handler(message):
    user_id = message.from_user.id
    ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    ref_count = len(referral_data.get(str(user_id), []))
    bot.send_message(message.chat.id, f"👥 **سیستم زیرمجموعه‌گیری**\n\n🔗 لینک دعوت شما:\n`{ref_link}`\n\n👤 تعداد زیرمجموعه‌ها: **{ref_count} نفر**\n🎁 با هر دعوت موفق، **۵,۰۰۰ تومان** هدیه بگیرید!", reply_markup=main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "📞 پشتیبانی")
def support_handler(message):
    bot.send_message(message.chat.id, "📞 لطفاً یکی از بخش‌های پشتیبانی زیر را انتخاب کنید:", reply_markup=support_keyboard())

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
    
    if call.from_user.id not in user_orders:
        user_orders[call.from_user.id] = {}
    user_orders[call.from_user.id]["plan"] = PLANS[plan_id]

    # اگر کاربر در حال تمدید سرویس قبلی خودش باشد، نام کاربری از قبل وجود دارد
    if "username" in user_orders[call.from_user.id] and user_orders[call.from_user.id].get("selected_service_index") is not None:
        selected_plan = PLANS[plan_id]
        invoice_text = (
            f"🧾 فاکتور تمدید سرویس (LUCIFER VPN)\n\n"
            f"📌 نام کاربری: `{user_orders[call.from_user.id]['username']}`\n"
            f"📦 سرویس جدید: {selected_plan['name']}\n"
            f"💰 قیمت: {selected_plan['price']}\n\n"
            f"روش پرداخت را انتخاب کنید:"
        )
        bot.edit_message_text(invoice_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=payment_method_keyboard(), parse_mode="Markdown")
    else:
        msg = bot.edit_message_text(
            f"شما پلن {PLANS[plan_id]['name']} را انتخاب کردید.\n\n"
            f"لطفاً نام کاربری انگلیسی دلخواه ارسال کنید:",
            chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_username)

def process_username(message):
    user_id = message.from_user.id
    if user_id not in user_orders:
        user_orders[user_id] = {}
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
    
    current_bal = user_wallets.get(str(user_id), 0)
    if current_bal < price:
        bot.answer_callback_query(call.id, "❌ موجودی کیف پول کافی نیست.", show_alert=True)
        return

    user_wallets[str(user_id)] = current_bal - price
    save_json(WALLETS_FILE, user_wallets)
    bot.answer_callback_query(call.id, "در حال پردازش...")

    success, result = create_panel_client(order["username"], plan["volume"], plan["days"])
    if success:
        if str(user_id) not in user_services_db:
            user_services_db[str(user_id)] = []
        
        # بررسی اینکه آیا سرویس تمدید بوده یا جدید
        found = False
        for s in user_services_db[str(user_id)]:
            if s["username"] == order["username"]:
                s["plan_name"] = plan["name"]
                s["sub_url"] = result
                found = True
                break
        if not found:
            user_services_db[str(user_id)].append({
                "username": order["username"],
                "plan_name": plan["name"],
                "sub_url": result,
                "volume": plan["volume"],
                "days": plan["days"]
            })
        save_json(SERVICES_FILE, user_services_db)

        success_msg = (
            f"🎉 خرید / تمدید موفق با کیف پول انجام شد!\n\n"
            f"👤 نام کاربری: `{order['username']}`\n\n"
            f"🔑 لینک اشتراک (ساب):\n`{result}`"
        )
        bot.send_message(user_id, success_msg, reply_markup=main_keyboard(), parse_mode="Markdown")
    else:
        user_wallets[str(user_id)] += price
        save_json(WALLETS_FILE, user_wallets)
        bot.send_message(user_id, f"❌ خطا در ساخت اکانت:\n{result}", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "pay_card")
def pay_via_card(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    order = user_orders.get(user_id)
    price = order["plan"]["price"]
    msg = bot.send_message(
        call.message.chat.id,
        f"💳 شماره کارت:\n`{CARD_NUMBER}`\nبه نام: **{CARD_HOLDER}**\nمبلغ: {price}\n\n📸 لطفاً تصویر رسید پرداخت را ارسال کنید.",
        parse_mode="Markdown"
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
        f"📥 رسید جدید خرید/تمدید\n"
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
        if str(user_id) not in user_services_db:
            user_services_db[str(user_id)] = []
        
        found = False
        for s in user_services_db[str(user_id)]:
            if s["username"] == order_info["username"]:
                s["plan_name"] = order_info["plan"]["name"]
                s["sub_url"] = result
                found = True
                break
        if not found:
            user_services_db[str(user_id)].append({
                "username": order_info["username"],
                "plan_name": order_info["plan"]["name"],
                "sub_url": result,
                "volume": order_info["plan"]["volume"],
                "days": order_info["plan"]["days"]
            })
        save_json(SERVICES_FILE, user_services_db)

        user_msg = (
            f"🎉 پرداخت شما توسط ادمین تایید شد!\n\n"
            f"👤 نام کاربری: `{order_info['username']}`\n\n"
            f"🔑 لینک اشتراک (ساب) شما:\n`{result}`"
        )
        bot.send_message(user_id, user_msg, reply_markup=main_keyboard(), parse_mode="Markdown")
        bot.edit_message_caption(call.message.caption + f"\n\n✅ تایید شد و اکانت ساخته شد.", chat_id=call.message.chat.id, message_id=call.message.message_id)
    else:
        bot.send_message(call.message.chat.id, f"❌ خطا در ساخت اکانت هنگام تایید:\n{result}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_order(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    user_id = int(call.data.replace("reject_", ""))
    bot.answer_callback_query(call.id, "سفارش رد شد.")
    bot.send_message(user_id, "❌ رسید پرداخت شما توسط ادمین تایید نشد.", reply_markup=main_keyboard())
    bot.edit_message_caption(call.message.caption + f"\n\n❌ رد شد.", chat_id=call.message.chat.id, message_id=call.message.message_id)

if __name__ == "__main__":
    keep_alive()
    print("🤖 ربات روشن شد...")
    bot.infinity_polling()
