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
BOT_TOKEN = "8735674807:AAG3lUzjXyzFLigtXvDrQa1KzX5HDiWfHM4"
bot = telebot.TeleBot(BOT_TOKEN)

ADMIN_IDS = [8738097569, 7384095755]
CARD_NUMBER = "5859831139452311"
CARD_HOLDER = "امید جوادی"
REFERRAL_BONUS = 5000  # مبلغ هدیه زیرمجموعه‌گیری به تومان

# ==================== مدیریت فایل‌ها (کیف پول، تست‌ها، تخفیف‌ها) ====================
WALLET_FILE = "wallets.json"
FREE_TEST_FILE = "free_tests.json"
COUPONS_FILE = "coupons.json"

def load_json(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return {int(k) if file_path == WALLET_FILE else k: v for k, v in json.load(f).items()}
        except Exception:
            return {}
    return {}

def save_json(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"خطا در ذخیره فایل {file_path}: {e}")

user_wallets = load_json(WALLET_FILE)
free_tested_users = load_json(FREE_TEST_FILE)

def load_coupons():
    if os.path.exists(COUPONS_FILE):
        try:
            with open(COUPONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {"LUCIFER": 10000} # کد تخفیف پیش‌فرض

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

# ==================== توابع کمکی ====================
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
            timeout=12, verify=False
        )
        if login_res.status_code == 200:
            token = login_res.json().get("access_token")
            headers["Authorization"] = f"Bearer {token}"
        else:
            login_res = session.post(
                f"{PANEL_URL}/api/admin/token",
                json={"username": PANEL_USERNAME, "password": PANEL_PASSWORD},
                timeout=12, verify=False
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

# ==================== کیبورد اصلی (طبق چیدمان درخواستی شما) ====================
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton("🛒 خرید سرویس جدید"),
        types.KeyboardButton("📦 سرویس‌های من")
    )
    markup.row(
        types.KeyboardButton("🎁 تست رایگان")
    )
    markup.row(
        types.KeyboardButton("💼 کیف پول"),
        types.KeyboardButton("🏷️ ثبت کد تخفیف")
    )
    markup.row(
        types.KeyboardButton("👥 زیرمجموعه‌گیری"),
        types.KeyboardButton("👤 حساب کاربری")
    )
    markup.row(
        types.KeyboardButton("📞 پشتیبانی")
    )
    return markup

def plans_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    buttons = []
    for plan_id, plan_info in PLANS.items():
        text = f"{plan_info['name']} ⟵ {plan_info['price']}"
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
    user_id = message.from_user.id
    args = message.text.split()
    
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id != user_id:
            user_orders[user_id] = user_orders.get(user_id, {})
            user_orders[user_id]["referrer"] = referrer_id

    welcome_text = f"سلام {message.from_user.first_name} عزیز! 🌹\nبه ربات LUCIFER VPN خوش آمدید.\n\nاز منوی زیر می‌توانید سرویس تهیه کنید یا تست رایگان بگیرید."
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard(), parse_mode="Markdown")

# ---------- تست رایگان ----------
@bot.message_handler(func=lambda msg: msg.text == "🎁 تست رایگان")
def free_test_handler(message):
    user_id = message.from_user.id
    if user_id in free_tested_users:
        bot.send_message(message.chat.id, "❌ شما قبلاً از تست رایگان استفاده کرده‌اید و هر کاربر فقط یک بار می‌تواند تست دریافت کند.")
        return

    bot.send_message(message.chat.id, "⏳ در حال ساخت تست رایگان ۱ ساعته (۲۵ مگابایت)... لطفاً صبر کنید.")
    
    test_username = f"test_{user_id}_{int(time.time())}"
    success, result = create_panel_client(username=test_username, volume_gb=0.024, days=0.04)

    if success:
        free_tested_users[user_id] = True
        save_json(FREE_TEST_FILE, free_tested_users)
        
        user_msg = f"🎁 **تست رایگان شما با موفقیت ساخته شد!**\n\n⏰ مدت اعتبار: ۱ ساعت\n📦 حجم: ۲۵ مگابایت\n\n🔑 لینک اشتراک:\n`{result}`"
        qr_photo = generate_qr_code(result)
        bot.send_photo(message.chat.id, qr_photo, caption=user_msg, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, f"❌ خطا در ساخت تست رایگان:\n{result}")

# ---------- کیف پول ----------
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
    save_json(WALLET_FILE, user_wallets)

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

# ---------- زیرمجموعه‌گیری ----------
@bot.message_handler(func=lambda msg: msg.text == "👥 زیرمجموعه‌گیری")
def referral_handler(message):
    user_id = message.from_user.id
    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    ref_text = (
        f"👥 **سیستم زیرمجموعه‌گیری و دعوت از دوستان**\n\n"
        f"با دعوت دوستان خود به ربات، به ازای هر خرید آن‌ها، هدیه نقدی به کیف پول خود دریافت کنید!\n\n"
        f"🔗 لینک دعوت اختصاصی شما:\n`{ref_link}`"
    )
    bot.send_message(message.chat.id, ref_text, parse_mode="Markdown")

# ---------- ثبت کد تخفیف ----------
@bot.message_handler(func=lambda msg: msg.text == "🏷️ ثبت کد تخفیف")
def coupon_menu_handler(message):
    msg = bot.send_message(
        message.chat.id, 
        "🏷️ لطفاً کد تخفیف خود را ارسال کنید تا روی خرید بعدی شما اعمال شود:"
    )
    bot.register_next_step_handler(msg, process_global_coupon)

def process_global_coupon(message):
    user_id = message.from_user.id
    code = message.text.strip()
    coupons = load_coupons()
    
    if code in coupons:
        discount_amount = coupons[code]
        user_orders[user_id] = user_orders.get(user_id, {})
        user_orders[user_id]["discount"] = discount_amount
        bot.send_message(
            message.chat.id, 
            f"✅ کد تخفیف `{code}` با موفقیت ثبت شد!\nمبلغ **{discount_amount:,} تومان** تخفیف روی خرید بعدی شما اعمال خواهد شد."
        )
    else:
        bot.send_message(message.chat.id, "❌ کد تخفیف وارد شده نامعتبر یا منقضی شده است.")

# ---------- حساب کاربری ----------
@bot.message_handler(func=lambda msg: msg.text == "👤 حساب کاربری")
def account_handler(message):
    user_id = message.from_user.id
    balance = user_wallets.get(user_id, 0)
    acc_text = (
        f"👤 **اطلاعات حساب کاربری شما**\n\n"
        f"🆔 آیدی عددی: `{user_id}`\n"
        f"💰 موجودی کیف پول: **{balance:,} تومان**\n"
        f"🎁 وضعیت تست رایگان: {'استفاده شده ❌' if user_id in free_tested_users else 'استفاده نشده ✅'}"
    )
    bot.send_message(message.chat.id, acc_text, parse_mode="Markdown")

# ---------- استعلام سرویس من ----------
@bot.message_handler(func=lambda msg: msg.text == "📦 سرویس‌های من")
def my_services_handler(message):
    bot.send_message(message.chat.id, "📊 برای استعلام وضعیت و حجم مصرفی، لطفاً نام کاربری اشتراک خود را ارسال کنید:")
    bot.register_next_step_handler(message, process_check_service)

def process_check_service(message):
    username = message.text.strip()
    session = requests.Session()
    try:
        login_res = session.post(f"{PANEL_URL}/api/admin/token", json={"username": PANEL_USERNAME, "password": PANEL_PASSWORD}, timeout=10, verify=False)
        if login_res.status_code == 200:
            token = login_res.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            res = session.get(f"{PANEL_URL}/api/user/{username}", headers=headers, timeout=10, verify=False)
            if res.status_code == 200:
                data = res.json()
                used_gb = data.get("used_bytes", 0) / (1024**3)
                total_gb = data.get("data_limit", 0) / (1024**3)
                status = data.get("status", "نامشخص")
                info_text = (
                    f"📊 **وضعیت سرویس: `{username}`**\n\n"
                    f"🟢 وضعیت: {status}\n"
                    f"📈 مصرف شده: {used_gb:.2f} گیگابایت\n"
                    f"📦 کل حجم: {total_gb:.2f} گیگابایت"
                )
                bot.send_message(message.chat.id, info_text, parse_mode="Markdown")
                return
    except Exception:
        pass
    bot.send_message(message.chat.id, "❌ کاربری با این نام در پنل یافت نشد یا خطا در برقراری ارتباط رخ داد.")

# ---------- خرید سرویس جدید ----------
@bot.message_handler(func=lambda msg: msg.text == "🛒 خرید سرویس جدید")
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
    user_id = call.from_user.id
    current_discount = user_orders.get(user_id, {}).get("discount", 0)
    
    user_orders[user_id] = {"plan": PLANS[plan_id], "discount": current_discount}

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
    discount = user_orders[user_id].get("discount", 0)
    final_price = max(0, selected_plan["price_num"] - discount)

    invoice_text = (
        f"🧾 **فاکتور سفارش (LUCIFER VPN)**\n\n"
        f"📌 نام کاربری: `{username_input}`\n"
        f"📦 سرویس: **{selected_plan['name']}**\n"
        f"💰 قیمت اصلی: **{selected_plan['price']}**\n"
        f"🏷️ تخفیف اعمال شده: **{discount:,} تومان**\n"
        f"💵 مبلغ قابل پرداخت: **{final_price:,} تومان**\n\n"
        f"💰 موجودی کیف پول شما: **{balance:,} تومان**\n\n"
        f"لطفاً روش پرداخت را انتخاب کنید:"
    )
    bot.send_message(message.chat.id, 
