import os
import telebot
from telebot import types
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN", "8979642001:AAG3Eanke57GW0XI9Gvo89VhaNLkU0geV24")
OWNER_ID = int(os.getenv("OWNER_ID", "8305397892"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://emowrxzckktfmlqhkoxk.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtb3dyeHpja2t0Zm1scWhrb3hrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc5NzY0NjAsImV4cCI6MjEwMzU1MjQ2MH0.tNVyZFLk9OZ4Kc0_cPoUKX5unYfCM6JiqG_NamZD1yw")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
user_session = {}

PAYMENT_METHODS = {
    "kpay": {
        "title": "KBZPay (KPay)",
        "number": "09400517227",
        "name": "Zin Mar Win"
    },
    "wave": {
        "title": "WavePay",
        "number": "09940391862",
        "name": "Ohn Mar Lwin"
    }
}

def get_headers():
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }

def find_user_by_telegram_id(tg_id):
    try:
        res = requests.get(
            f"{SUPABASE_URL}/rest/v1/profiles?telegram_id=eq.{tg_id}&select=*",
            headers=get_headers()
        )
        if res.ok:
            data = res.json()
            if data and len(data) > 0:
                return data[0]
    except Exception as e:
        print(f"Error fetching user: {e}")
    return None

def find_user_by_username(username):
    try:
        res = requests.get(
            f"{SUPABASE_URL}/rest/v1/profiles?username=eq.{username}&select=*",
            headers=get_headers()
        )
        if res.ok:
            data = res.json()
            if data and len(data) > 0:
                return data[0]
    except Exception as e:
        print(f"Error fetching username: {e}")
    return None

def link_telegram_id(username, tg_id):
    try:
        res = requests.patch(
            f"{SUPABASE_URL}/rest/v1/profiles?username=eq.{username}",
            headers=get_headers(),
            json={"telegram_id": str(tg_id)}
        )
        return res.ok
    except Exception:
        return False

def show_main_menu(chat_id, username, balance):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_topup = types.InlineKeyboardButton("💳 ငွေဖြည့်မည်", callback_data="menu_topup")
    btn_change = types.InlineKeyboardButton("⚙️ Username ပြောင်းမည်", callback_data="menu_change_user")
    markup.add(btn_topup, btn_change)

    msg = (
        f"👋 မင်္ဂလာပါ <b>@{username}</b>\n\n"
        f"💰 လက်ကျန်ငွေ: <b>{balance:,.0f} Ks</b>\n\n"
        f"အောက်ပါခလုတ်ကိုနှိပ်၍ ငွေဖြည့်သွင်းနိုင်ပါသည် 👇"
    )
    bot.send_message(chat_id, msg, reply_markup=markup)

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    user = find_user_by_telegram_id(chat_id)

    if user:
        show_main_menu(chat_id, user.get('username'), float(user.get('balance', 0)))
    else:
        user_session[chat_id] = {"step": "await_username"}
        bot.send_message(
            chat_id,
            "👋 <b>StarGrow Boost မှ ကြိုဆိုပါသည်!</b>\n\n"
            "သင့် Telegram အကောင့်နှင့် ချိတ်ဆက်ရန် StarGrow ဝဘ်ဆိုဒ်တွင် ဖွင့်ထားသော <b>Username</b> ကို ရိုက်ပို့ပေးပါ:"
        )

@bot.message_handler(func=lambda msg: msg.chat.id in user_session and msg.text and not msg.text.startswith('/'))
def handle_text_inputs(message):
    chat_id = message.chat.id
    state = user_session[chat_id].get("step")

    if state == "await_username":
        input_uname = message.text.strip().replace('@', '')
        user = find_user_by_username(input_uname)

        if not user:
            bot.send_message(chat_id, f"❌ <b>@{input_uname}</b> အမည်ဖြင့် ဝဘ်ဆိုဒ်တွင် အကောင့်ရှာမတွေ့ပါ။ Username မှန်ကန်စွာ ပြန်လည်ရိုက်ပို့ပေးပါ:")
            return

        link_telegram_id(input_uname, chat_id)
        user_session[chat_id] = {"username": input_uname}
        bot.send_message(chat_id, f"✅ <b>@{input_uname}</b> အကောင့်အား အောင်မြင်စွာ ချိတ်ဆက်ပြီးပါပြီ!")
        show_main_menu(chat_id, input_uname, float(user.get('balance', 0)))

    elif state == "await_amount":
        try:
            amt = float(message.text.strip())
            if amt <= 0:
                raise ValueError()
            user_session[chat_id]["amount"] = amt
            user_session[chat_id]["step"] = "await_slip"
            bot.send_message(chat_id, "📸 ငွေလွှဲထားသော <b>ပြေစာ (Slip ဓာတ်ပုံ)</b> ကို ပို့ပေးပါ:")
        except ValueError:
            bot.send_message(chat_id, "⚠️ ကျေးဇူးပြု၍ ငွေပမာဏကို ဂဏန်းသီးသန့်သာ ရိုက်ပို့ပေးပါ (ဥပမာ: <code>5000</code>) :")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    session = user_session.get(chat_id)

    if session and session.get("step") == "await_slip":
        file_id = message.photo[-1].file_id
        username = session.get("username")
        amount = session.get("amount")
        method = session.get("method", "KPay")

        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_app = types.InlineKeyboardButton("✅ လက်ခံမည် (Approve)", callback_data=f"app:{username}:{amount}:{chat_id}")
        btn_rej = types.InlineKeyboardButton("❌ ငြင်းပယ်မည် (Reject)", callback_data=f"rej:{chat_id}")
        markup.add(btn_app, btn_rej)

        caption = (
            "📥 <b>ငွေဖြည့်သွင်းလွှာ အသစ်ရောက်ရှိပါသည်!</b>\n\n"
            f"👤 Username: <code>{username}</code>\n"
            f"💳 Payment: <b>{method}</b>\n"
            f"💰 ငွေပမာဏ: <b>{amount:,.0f} Ks</b>\n"
            f"🆔 Telegram ID: <code>{chat_id}</code>"
        )

        bot.send_photo(OWNER_ID, file_id, caption=caption, reply_markup=markup)
        bot.send_message(chat_id, "✅ <b>ပြေစာ ပေးပို့မှု အောင်မြင်ပါသည်!</b>\n\nAdmin မှ စစ်ဆေးအတည်ပြုပြီးပါက သင့်အကောင့်ထဲသို့ ငွေချက်ချင်း ရောက်ရှိသွားပါမည်။")
        user_session[chat_id] = {"username": username}

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "menu_topup":
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_kpay = types.InlineKeyboardButton("🟢 KPay", callback_data="pay_kpay")
        btn_wave = types.InlineKeyboardButton("🟡 WavePay", callback_data="pay_wave")
        markup.add(btn_kpay, btn_wave)
        bot.edit_message_text("ငွေပေးချေမည့်နည်းလမ်း ရွေးချယ်ပါ 👇", chat_id, call.message.message_id, reply_markup=markup)

    elif data in ["pay_kpay", "pay_wave"]:
        method_key = "kpay" if data == "pay_kpay" else "wave"
        info = PAYMENT_METHODS[method_key]
        
        user = find_user_by_telegram_id(chat_id)
        uname = user.get('username') if user else user_session.get(chat_id, {}).get('username')

        user_session[chat_id] = {
            "step": "await_amount",
            "username": uname,
            "method": info["title"]
        }

        msg = (
            f"📌 <b>{info['title']} အချက်အလက်:</b>\n\n"
            f"📱 ဖုန်းနံပါတ်: <code>{info['number']}</code>\n"
            f"👤 အမည်: <b>{info['name']}</b>\n\n"
            f"ငွေလွှဲပြီးပါက ဖြည့်သွင်းလိုသော <b>ငွေပမာဏ (ကျပ်)</b> ကို ရိုက်ပို့ပေးပါ (ဥပမာ: <code>5000</code>) :"
        )
        bot.send_message(chat_id, msg)

    elif data == "menu_change_user":
        user_session[chat_id] = {"step": "await_username"}
        bot.send_message(chat_id, "ပြောင်းလဲအသုံးပြုလိုသော StarGrow <b>Username</b> အသစ်ကို ရိုက်ပို့ပေးပါ:")

    elif data.startswith("app:"):
        if call.from_user.id != OWNER_ID:
            bot.answer_callback_query(call.id, "❌ သင်သည် Admin မဟုတ်ပါ!", show_alert=True)
            return

        _, username, amount_str, target_tg_id = data.split(":")
        amount = float(amount_str)

        try:
            res = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/approve_topup_by_username",
                headers=get_headers(),
                json={"p_username": username, "p_amount": amount}
            )

            if res.status_code == 200:
                new_bal = res.json()
                bot.edit_message_caption(
                    chat_id=OWNER_ID,
                    message_id=call.message.message_id,
                    caption=f"{call.message.caption}\n\n✅ <b>အတည်ပြုပြီး (Approved)</b>\n💳 လက်ကျန်ငွေသစ်: <b>{float(new_bal):,.0f} Ks</b>",
                    reply_markup=None
                )
                bot.send_message(
                    target_tg_id,
                    f"🎉 <b>ငွေဖြည့်သွင်းမှု အောင်မြင်ပါသည်!</b>\n\n"
                    f"သင့်အကောင့် <code>@{username}</code> ထဲသို့ <b>{amount:,.0f} Ks</b> ထည့်သွင်းပေးပြီးပါပြီ။ StarGrow Boost တွင် အော်ဒါများ တင်နိုင်ပါပြီခင်ဗျာ။"
                )
                bot.answer_callback_query(call.id, "ငွေထည့်သွင်းပြီးပါပြီ!")
        except Exception as e:
            bot.answer_callback_query(call.id, f"Error: {e}", show_alert=True)

    elif data.startswith("rej:"):
        if call.from_user.id != OWNER_ID:
            bot.answer_callback_query(call.id, "❌ သင်သည် Admin မဟုတ်ပါ!", show_alert=True)
            return

        _, target_tg_id = data.split(":")
        bot.edit_message_caption(
            chat_id=OWNER_ID,
            message_id=call.message.message_id,
            caption=f"{call.message.caption}\n\n❌ <b>ငြင်းပယ်လိုက်ပါပြီ (Rejected)</b>",
            reply_markup=None
        )
        bot.send_message(
            target_tg_id,
            "❌ <b>သင့်ငွေဖြည့်သွင်းမှု ငြင်းပယ်ခံရပါသည်!</b>\n\nပြေစာ မမှန်ကန်ခြင်း သို့မဟုတ် ငွေလွှဲမရောက်ရှိခြင်းကြောင့် ဖြစ်နိုင်ပါသည်။"
        )
        bot.answer_callback_query(call.id, "ငြင်းပယ်ပြီးပါပြီ")

if __name__ == '__main__':
    print("🚀 StarGrow Telegram Bot is running...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
        
