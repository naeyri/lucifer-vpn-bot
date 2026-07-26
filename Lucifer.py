import telebot
from telebot import types
import requests
import json
import os
import time
from flask import Flask
import threading
import urllib3
from datetime import datetime

# غیرفعال کردن اخطار SSL در صورت خودایمن نبودن گواهی پنل
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== تنظیمات وب سرور جهت روشن ماندن 24 ساعته ====================
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.start()

# ==================== تنظیمات عمومی ====================
BOT_TOKEN = "8735674807:AAG3lUzjXyzFLigtXvDrQa1KzX5HDiWfHM4"
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_IDS = [8738097569, 7384095755]
CARD_NUMBER = "5859831139452311"
CARD_HOLDER = "امید جوادی"
SUPPORT_ID = "@naeyri1"

# ==================== مسیر فایل‌های ذخیره‌سازی ====================
WALLETS_FILE = "wallets.json"
FREE_TEST_FILE = "free_tested.json"
REFERRALS_FILE = "referrals.json"
USER_SERVICES_FILE = "user_services.json"

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
user_services = load_json(USER_SERVICES_FILE)

# ==================== تنظیمات پنل مرزبان و پلن‌ها ====================
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

EXTRA_VOLUMES = {
    "ex_5": {"name": "۵ گیگابایت اضافه", "price": 20000, "volume": 5},
    "ex_10": {"name": "۱۰ گیگابایت اضافه", "price": 35000, "volume": 10},
    "ex_20": {"name": "۲۰ گیگابایت اضافه", "price": 60000, "volume": 20},
}

user_orders = {}
deposit_requests = {}

def get_marzban_token():
    url = f"{PANEL_URL}/api/admin/token"
    data = {"username": PANEL_USERNAME, "password": PANEL_PASSWORD}
    headers = {"Content-Type": "application/x-www-form-urlencoded", "accept": "application/json"}
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
        return False, "خطا در احراز هویت با پنل مرزبان."

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "accept": "application/json"}
    expire_timestamp = int(time.time()) + (days * 86400) if days > 0 else None
    total_bytes = int(volume_gb * 1024 * 1024 * 1024) if volume_gb > 0 else 0

    payload = {
        "username": username,
        "proxies": {"vless": {}, "vmess": {}, "trojan": {}},
        "inbounds": {"vless": ["VLESS + TLS", "VLESS TCP"], "vmess": ["VMess TCP"], "trojan": ["Trojan TCP"]},
        "expire": expire_timestamp,
        "data_limit": total_bytes,
        "data_limit_reset_strategy": "no_reset"
    }

    for url in [f"{PANEL_URL}/api/users", f"{PANEL_URL}/api/user"]:
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15, verify=False)
            if response.status_code in [200, 201]:
                user_data = response.json()
                sub_url = user_data.get("subscription_url") or f"{PANEL_URL}/sub/{username}"
                return True, sub_url
            elif response.status_code == 404:
                continue
            else:
                return False, f"پاسخ پنل: {response.text}"
        except:
            continue
    return False, "مسیر ساخت کاربر در پنل یافت نشد."

def get_user_panel_info(username):
    token = get_marzban_token()
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}
    try:
        response = requests.get(f"{PANEL_URL}/api/user/{username}", headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def modify_user_in_panel(username, add_volume_gb=0, add_days=0):
    token = get_marzban_token()
    if not token:
        return False, "خطا در اتصال به پنل"
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "accept": "application/json"}
    user_info = get_user_panel_info(username)
    if not user_info:
        return False, "کاربر در پنل یافت نشد."
    
    current_expire = user_info.get("expire")
    current_limit = user_info.get("data_limit") or 0
    
    new_expire = current_expire
    if add_days > 0:
        base_time = current_expire if (current_expire and current_expire > time.time()) else time.time()
        new_expire = int(base_time) + (add_days * 86400)
        
    new_limit = current_limit
    if add_volume_gb > 0:
        added_bytes = int(add_volume_gb * 1024 * 1024 * 1024)
        new_limit = current_limit + added_bytes

    payload = {"expire": new_expire, "data_limit": new_limit}
    try:
        response = requests.put(f"{PANEL_URL}/api/user/{username}", json=payload, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            return True, "عملیات با موفقیت انجام شد."
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)
        # ==================== کیبوردها ====================
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🛒 خرید سرویس"), types.KeyboardButton("📦 سرویس‌های من"))
    markup.row(types.KeyboardButton("🎁 تست رایگان"), types.KeyboardButton("💼 کیف پول"))
    markup.row(types.KeyboardButton("👥 زیرمجموعه‌گیری"), types.KeyboardButton("📞 پشتیبانی"))
    return markup

def plans_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=f"{info['name']} - {info['price']}", callback_data=f"buy_{pid}") for pid, info in PLANS.items()]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("❌ انصراف", callback_data="cancel_order"))
    return markup

def payment_method_keyboard(action_type="buy"):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👛 پرداخت از کیف پول", callback_data=f"pay_wallet_{action_type}"),
        types.InlineKeyboardButton("💳 کارت به کارت", callback_data=f"pay_card_{action_type}"),
        types.InlineKeyboardButton("❌ انصراف", callback_data="cancel_order")
    )
    return markup

def wallet_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ شارژ کیف پول", callback_data="charge_wallet"))
    return markup

def admin_receipt_keyboard(user_id, action_type="buy"):
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ تایید و اعمال", callback_data=f"approve_{action_type}_{user_id}"),
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

# ==================== هندلرها ====================
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
                    user_wallets[str(referrer_id)] = user_wallets.get(str(referrer_id), 0) + 5000
                    save_json(WALLETS_FILE, user_wallets)
                    try:
                        bot.send_message(referrer_id, "🎉 یک زیرمجموعه جدید ثبت شد! مبلغ ۵,۰۰۰ تومان به کیف پولت اضافه شد.")
                    except:
                        pass
        except:
            pass

    welcome_text = "به دنیای ارتباط امن و پرسرعت **LUCIFER VPN** خوش آمدید! 🚀⚡️\n\nاز منوی زیر برای مدیریت سرویس‌ها و خرید استفاده کنید 👇"
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard(), parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🛒 خرید سرویس")
def show_plans(message):
    bot.send_message(message.chat.id, "لطفاً پلن مورد نظر خود را انتخاب کنید:", reply_markup=plans_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "🎁 تست رایگان")
def free_test_handler(message):
    user_id = message.from_user.id
    if str(user_id) in free_tested_users:
        bot.send_message(message.chat.id, "❌ شما قبلاً از تست رایگان استفاده کرده‌اید.", reply_markup=main_keyboard())
        return

    bot.send_message(message.chat.id, "⏳ در حال ساخت تست رایگان...")
    test_username = f"test_{user_id}_{int(time.time())}"
    success, result = create_panel_client(username=test_username, volume_gb=0.0244, days=1)

    if success:
        free_tested_users[str(user_id)] = True
        save_json(FREE_TEST_FILE, free_tested_users)
        
        if str(user_id) not in user_services:
            user_services[str(user_id)] = []
        user_services[str(user_id)].append({
            "username": test_username, "plan_name": "تست رایگان", "volume": 0.0244, "days": 1, "price": 0, "sub_url": result
        })
        save_json(USER_SERVICES_FILE, user_services)

        test_msg = f"🎁 **تست رایگان با موفقیت ساخته شد!**\n\n👤 نام کاربری: `{test_username}`\n🔑 لینک اشتراک:\n`{result}`"
        bot.send_message(message.chat.id, test_msg, reply_markup=main_keyboard(), parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❌ خطا در ساخت تست رایگان:\n{result}", reply_markup=main_keyboard())

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
    
    user_wallets[str(user_id)] = user_wallets.get(str(user_id), 0) + amount
    save_json(WALLETS_FILE, user_wallets)
    
    bot.answer_callback_query(call.id, "کیف پول کاربر شارژ شد.")
    bot.send_message(user_id, f"🎉 پرداخت شما تایید شد!\n💰 مبلغ {amount:,} تومان به کیف پول شما اضافه شد.", reply_markup=main_keyboard())
    bot.edit_message_caption(call.message.caption + f"\n\n✅ تایید شد.", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deprej_"))
def reject_deposit(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    user_id = int(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "درخواست رد شد.")
    bot.send_message(user_id, "❌ رسید شارژ کیف پول شما تایید نشد.", reply_markup=main_keyboard())
    bot.edit_message_caption(call.message.caption + "\n\n❌ رد شد.", chat_id=call.message.chat.id, message_id=call.message.message_id)

# ==================== مدیریت سرویس‌ها و عملیات تکمیلی ====================
@bot.message_handler(func=lambda msg: msg.text == "📦 سرویس‌های من")
def show_user_services(message):
    user_id = str(message.from_user.id)
    services = user_services.get(user_id, [])
    
    if not services:
        bot.send_message(message.chat.id, "❌ شما هیچ سرویس فعالی ندارید.", reply_markup=main_keyboard())
        return

    for idx, s in enumerate(services):
        username = s["username"]
        panel_info = get_user_panel_info(username)
        
        if panel_info:
            used_traffic = panel_info.get("used_traffic", 0) / (1024**3)
            data_limit = panel_info.get("data_limit", 0) / (1024**3) if panel_info.get("data_limit") else "نامحدود"
            expire_ts = panel_info.get("expire")
            
            if expire_ts:
                expire_date = datetime.fromtimestamp(expire_ts).strftime('%Y-%m-%d %H:%M')
                days_left = max(0, int((expire_ts - time.time()) / 86400))
            else:
                expire_date = "دائمی / نامحدود"
                days_left = "∞"
                
            status_text = panel_info.get("status", "active")
        else:
            used_traffic, data_limit, expire_date, days_left, status_text = 0, "نامشخص", "نامشخص", 0, "unknown"

        text = (
            f"📦 **سرویس شماره {idx+1}**\n"
            f"👤 نام کاربری: `{username}`\n"
            f"📊 وضعیت: `{status_text}`\n"
            f"📥 حجم مصرفی: `{used_traffic:.2f} گیگابایت` از `{data_limit}`\n"
            f"⏳ انقضا: `{expire_date}` (حدود {days_left} روز دیگر)\n"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔗 دریافت لینک ساب", callback_data=f"sub_{username}"),
            types.InlineKeyboardButton("🔄 تمدید سرویس", callback_data=f"renew_{username}"),
            types.InlineKeyboardButton("➕ خرید حجم اضافه", callback_data=f"extravol_{username}")
        )
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def send_subscription_link(call):
    username = call.data.replace("sub_", "")
    panel_info = get_user_panel_info(username)
    if panel_info:
        sub_url = panel_info.get("subscription_url") or f"{PANEL_URL}/sub/{username}"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"🔑 لینک اشتراک شما برای `{username}`:\n`{sub_url}`", parse_mode="Markdown")
    else:
        bot.answer_callback_query(call.id, "خطا در دریافت اطلاعات از پنل.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("renew_"))
def renew_service_menu(call):
    username = call.data.replace("renew_", "")
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    for pid, info in PLANS.items():
        markup.add(types.InlineKeyboardButton(text=f"{info['name']} - {info['price']}", callback_data=f"dorenew_{username}_{pid}"))
    markup.add(types.InlineKeyboardButton("❌ انصراف", callback_data="cancel_order"))
    bot.send_message(call.message.chat.id, f"لطفاً پلن مورد نظر برای تمدید `{username}` را انتخاب کنید:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("dorenew_"))
def process_renewal(call):
    _, username, pid = call.data.split("_")
    plan = PLANS[pid]
    user_id = call.from_user.id
    
    user_orders[user_id] = {"username": username, "plan": plan, "type": "renew"}
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"روش پرداخت تمدید سرویس `{username}` را انتخاب کنید:", reply_markup=payment_method_keyboard(action_type="renew"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("extravol_"))
def extra_volume_menu(call):
    username = call.data.replace("extravol_", "")
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ev_id, info in EXTRA_VOLUMES.items():
        markup.add(types.InlineKeyboardButton(text=f"{info['name']} - {info['price']:,} تومان", callback_data=f"doextra_{username}_{ev_id}"))
    markup.add(types.InlineKeyboardButton("❌ انصراف", callback_data="cancel_order"))
    bot.send_message(call.message.chat.id, f"انتخاب حجم اضافه برای `{username}`:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("doextra_"))
def process_extra_volume(call):
    _, username, ev_id = call.data.split("_")
    ev_info = EXTRA_VOLUMES[ev_id]
    user_id = call.from_user.id
    
    user_orders[user_id] = {"username": username, "ev_info": ev_info, "type": "extra"}
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"روش پرداخت حجم اضافه ({ev_info['name']}) را انتخاب کنید:", reply_markup=payment_method_keyboard(action_type="extra"))

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_wallet_"))
def pay_wallet_dispatcher(call):
    action_type = call.data.replace("pay_wallet_", "")
    user_id = call.from_user.id
    order = user_orders.get(user_id)
    if not order:
        return
    
    if action_type in ["buy", "renew"]:
        price = order["plan"]["price_num"]
    elif action_type == "extra":
        price = order["ev_info"]["price"]
    else:
        return

    current_bal = user_wallets.get(str(user_id), 0)
    if current_bal < price:
        bot.answer_callback_query(call.id, "❌ موجودی کیف پول کافی نیست.", show_alert=True)
        return

    user_wallets[str(user_id)] = current_bal - price
    save_json(WALLETS_FILE, user_wallets)
    bot.answer_callback_query(call.id, "در حال انجام عملیات...")

    if action_type == "buy":
        success, result = create_panel_client(order["username"], order["plan"]["volume"], order["plan"]["days"])
        if success:
            if str(user_id) not in user_services:
                user_services[str(user_id)] = []
            user_services[str(user_id)].append({"username": order["username"], "plan_name": order["plan"]["name"], "sub_url": result})
            save_json(USER_SERVICES_FILE, user_services)
            bot.send_message(user_id, f"🎉 خرید موفق!\n👤 نام کاربری: `{order['username']}`\n🔑 لینک اشتراک:\n`{result}`", parse_mode="Markdown")
        else:
            user_wallets[str(user_id)] += price
            save_json(WALLETS_FILE, user_wallets)
            bot.send_message(user_id, f"❌ خطا:\n{result}")

    elif action_type == "renew":
        success, msg = modify_user_in_panel(order["username"], add_volume_gb=order["plan"]["volume"], add_days=order["plan"]["days"])
        if success:
            bot.send_message(user_id, f"✅ سرویس `{order['username']}` با موفقیت تمدید شد.", parse_mode="Markdown", reply_markup=main_keyboard())
        else:
            user_wallets[str(user_id)] += price
            save_json(WALLETS_FILE, user_wallets)
            bot.send_message(user_id, f"❌ خطا در تمدید: {msg}")

    elif action_type == "extra":
        success, msg = modify_user_in_panel(order["username"], add_volume_gb=order["ev_info"]["volume"], add_days=0)
        if success:
            bot.send_message(user_id, f"✅ حجم اضافه با موفقیت به `{order['username']}` اعمال شد.", parse_mode="Markdown", reply_markup=main_keyboard())
        else:
            user_wallets[str(user_id)] += price
            save_json(WALLETS_FILE, user_wallets)
            bot.send_message(user_id, f"❌ خطا: {msg}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_card_"))
def pay_card_dispatcher(call):
    action_type = call.data.replace("pay_card_", "")
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    order = user_orders.get(user_id)
    
    if action_type in ["buy", "renew"]:
        price = order["plan"]["price"]
    else:
        price = f"{order['ev_info']['price']:,} تومان"

    msg = bot.send_message(
        call.message.chat.id,
        f"💳 شماره کارت:\n`{CARD_NUMBER}`\nبه نام: **{CARD_HOLDER}**\nمبلغ: {price}\n\n📸 لطفاً تصویر رسید پرداخت را ارسال کنید.",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, lambda m: process_receipt_dispatcher(m, action_type))

def process_receipt_dispatcher(message, action_type):
    user_id = message.from_user.id
    if not message.photo:
        msg = bot.send_message(message.chat.id, "❌ لطفاً فقط عکس رسید را ارسال کنید.")
        bot.register_next_step_handler(msg, lambda m: process_receipt_dispatcher(m, action_type))
        return

    order_info = user_orders.get(user_id)
    photo_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, "✅ رسید ارسال شد. پس از تایید ادمین، عملیات انجام می‌شود.", reply_markup=main_keyboard())

    admin_caption = (
        f"📥 رسید جدید ({action_type})\n"
        f"👤 کاربر: `{user_id}`\n"
        f"🔑 نام کاربری: `{order_info.get('username')}`"
    )

    for admin_id in ADMIN_IDS:
        try:
            bot.send_photo(admin_id, photo_id, caption=admin_caption, reply_markup=admin_receipt_keyboard(user_id, action_type), parse_mode="Markdown")
        except:
            pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve_dispatcher(call):
    if call.from_user.id not in ADMIN_IDS:
        return

    parts = call.data.split("_")
    action_type = parts[1]
    user_id = int(parts[2])
    order_info = user_orders.get(user_id)

    if not order_info:
        bot.answer_callback_query(call.id, "اطلاعات سفارش یافت نشد.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "در حال اعمال...")

    if action_type == "buy":
        success, result = create_panel_client(order_info["username"], order_info["plan"]["volume"], order_info["plan"]["days"])
        if success:
            if str(user_id) not in user_services:
                user_services[str(user_id)] = []
            user_services[str(user_id)].append({"username": order_info["username"], "plan_name": order_info["plan"]["name"], "sub_url": result})
            save_json(USER_SERVICES_FILE, user_services)
            bot.send_message(user_id, f"🎉 تایید شد!\n🔑 لینک اشتراک:\n`{result}`", parse_mode="Markdown", reply_markup=main_keyboard())
    elif action_type == "renew":
        success, _ = modify_user_in_panel(order_info["username"], add_volume_gb=order_info["plan"]["volume"], add_days=order_info["plan"]["days"])
        if success:
            bot.send_message(user_id, f"✅ سرویس `{order_info['username']}` تمدید شد.", parse_mode="Markdown", reply_markup=main_keyboard())
    elif action_type == "extra":
        success, _ = modify_user_in_panel(order_info["username"], add_volume_gb=order_info["ev_info"]["volume"], add_days=0)
        if success:
            bot.send_message(user_id, f"✅ حجم اضافه به `{order_info['username']}` اعمال شد.", parse_mode="Markdown", reply_markup=main_keyboard())

    bot.edit_message_caption(call.message.caption + "\n\n✅ تایید و اعمال شد.", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def reject_dispatcher(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    user_id = int(call.data.split("_")[1])
    bot.answer_callback_query(call.id, "سفارش رد شد.")
    bot.send_message(user_id, "❌ درخواست شما توسط ادمین تایید نشد.", reply_markup=main_keyboard())
    bot.edit_message_caption(call.message.caption + "\n\n❌ رد شد.", chat_id=call.message.chat.id, message_id=call.message.message_id)

@bot.message_handler(func=lambda msg: msg.text == "👥 زیرمجموعه‌گیری")
def referral_handler(message):
    user_id = message.from_user.id
    ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    ref_count = len(referral_data.get(str(user_id), []))
    bot.send_message(message.chat.id, f"👥 **سیستم زیرمجموعه‌گیری**\n\n🔗 لینک دعوت شما:\n`{ref_link}`\n\n👤 تعداد زیرمجموعه‌ها: **{ref_count} نفر**", parse_mode="Markdown", reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "📞 پشتیبانی")
def support_handler(message):
    bot.send_message(message.chat.id, f"📞 پشتیبانی: {SUPPORT_ID}", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "cancel_order")
def cancel_order(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text("عملیات لغو شد.", chat_id=call.message.chat.id, message_id=call.message.message_id)

if __name__ == "__main__":
    keep_alive()
    print("🤖 ربات پیشرفته LUCIFER VPN روشن شد...")
    bot.infinity_polling()
                                            
