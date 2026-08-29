import os
import telebot
from telebot import types
import requests

# Configurations (Railway Variables သို့မဟုတ် Direct Value)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8979642001:AAG3Eanke57GW0XI9Gvo89VhaNLkU0geV24")
OWNER_ID = int(os.getenv("OWNER_ID", "8305397892"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://emowrxzckktfmlqhkoxk.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtb3dyeHpja2t0Zm1scWhrb3hrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc5NzY0NjAsImV4cCI6MjEwMzU1MjQ2MH0.tNVyZFLk9OZ4Kc0_cPoUKX5unYfCM6JiqG_NamZD1yw")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
user_data = {}

@bot.message_handler(commands=['start', 'topup'])
def send_welcome(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'step': 'await_username'}
    
    msg_text = (
        "👋 <b>StarGrow Boost ငွေဖြည့်စနစ်မှ ကြိုဆိုပါသည်!</b>\n\n"
        "📌 <b>ငွေလွှဲရမည့် အကောင့် (KPay):</b>\n"
        "📱 ဖုန်းနံပါတ်: <code>09400517227</code>\n"
        "👤 နာမည်: <b>Zin Mar Win</b>\n\n"
        "👉 ငွေလွှဲပြီးပါက StarGrow Website တွင် ဖွင့်ထားသော သင်၏ <b>Username</b> ကို ရိုက်ပို့ပေးပါ:"
    )
    bot.send_message(chat_id, msg_text)

@bot.message_handler(func=lambda msg: msg.chat.id in user_data and msg.text and not msg.text.startswith('/'))
def handle_text(message):
    chat_id = message.chat.id
    state = user_data[chat_id].get('step')

    if state == 'await_username':
        user_data[chat_id]['username'] = message.text.strip()
        user_data[chat_id]['step'] = 'await_amount'
        bot.send_message(chat_id, "💰 ဖြည့်သွင်းလိုသော <b>ငွေပမာဏ (ကျပ်)</b> ကို ဂဏန်းချည်းသာ ရိုက်ပို့ပေးပါ (ဥပမာ: <code>5000</code>) :")
        
    elif state == 'await_amount':
        try:
            amt = float(message.text.strip())
            if amt <= 0:
                raise ValueError()
            user_data[chat_id]['amount'] = amt
            user_data[chat_id]['step'] = 'await_slip'
            bot.send_message(chat_id, "📸 ငွေလွှဲထားသော <b>ပြေစာ (Slip) ဓာတ်ပုံ</b> ကို ပို့ပေးပါ:")
        except ValueError:
            bot.send_message(chat_id, "⚠️ ကျေးဇူးပြု၍ ငွေပမာဏကို ဂဏန်းမှန်ကန်စွာ ရိုက်ပို့ပေးပါ:")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    if chat_id in user_data and user_data[chat_id].get('step') == 'await_slip':
        file_id = message.photo[-1].file_id
        username = user_data[chat_id]['username']
        amount = user_data[chat_id]['amount']

        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_approve = types.InlineKeyboardButton("✅ လက်ခံမည် (Approve)", callback_data=f"app:{username}:{amount}:{chat_id}")
        btn_reject = types.InlineKeyboardButton("❌ ငြင်းပယ်မည် (Reject)", callback_data=f"rej:{chat_id}")
        markup.add(btn_approve, btn_reject)

        caption = (
            "📥 <b>ငွေဖြည့်သွင်းလွှာ အသစ်ရောက်ရှိပါသည်!</b>\n\n"
            f"👤 Website Username: <code>{username}</code>\n"
            f"💰 ငွေပမာဏ: <b>{amount:,.0f} Ks</b>\n"
            f"🆔 Telegram ID: <code>{chat_id}</code>"
        )
        
        bot.send_photo(OWNER_ID, file_id, caption=caption, reply_markup=markup)
        bot.send_message(chat_id, "✅ <b>ပြေစာ ပေးပို့မှု အောင်မြင်ပါသည်!</b>\n\nAdmin မှ စစ်ဆေးအတည်ပြုပြီးပါက သင့် Website အကောင့်ထဲသို့ ငွေချက်ချင်း ရောက်ရှိသွားပါမည်။")
        del user_data[chat_id]

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.from_user.id != OWNER_ID:
        bot.answer_callback_query(call.id, "❌ သင်သည် Admin မဟုတ်ပါ!", show_alert=True)
        return

    data = call.data.split(":")
    action = data[0]

    if action == "app":
        username = data[1]
        amount = float(data[2])
        user_tg_id = data[3]

        try:
            headers = {
                "apikey": SUPABASE_ANON_KEY,
                "Content-Type": "application/json"
            }
            res = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/approve_topup_by_username",
                headers=headers,
                json={"p_username": username, "p_amount": amount}
            )

            if res.status_code == 200:
                new_balance = res.json()
                bot.edit_message_caption(
                    chat_id=OWNER_ID,
                    message_id=call.message.message_id,
                    caption=(
                        f"{call.message.caption}\n\n"
                        f"✅ <b>အတည်ပြုပြီးပါပြီ (Approved)</b>\n"
                        f"💳 User လက်ကျန်ငွေသစ်: <b>{float(new_balance):,.0f} Ks</b>"
                    ),
                    reply_markup=None
                )
                
                bot.send_message(
                    user_tg_id,
                    f"🎉 <b>ငွေဖြည့်သွင်းမှု အောင်မြင်ပါသည်!</b>\n\n"
                    f"သင့် Website အကောင့် <code>@{username}</code> ထဲသို့ <b>{amount:,.0f} Ks</b> ထည့်သွင်းပေးပြီးပါပြီ။ StarGrow Boost တွင် အော်ဒါများ စတင်တင်နိုင်ပါပြီခင်ဗျာ။"
                )
                bot.answer_callback_query(call.id, "ငွေထည့်သွင်းမှု အောင်မြင်ပါသည်!")
            else:
                bot.answer_callback_query(call.id, f"Supabase Error: {res.text}", show_alert=True)

        except Exception as e:
            bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)

    elif action == "rej":
        user_tg_id = data[1]
        bot.edit_message_caption(
            chat_id=OWNER_ID,
            message_id=call.message.message_id,
            caption=f"{call.message.caption}\n\n❌ <b>ငြင်းပယ်လိုက်ပါပြီ (Rejected)</b>",
            reply_markup=None
        )
        bot.send_message(
            user_tg_id,
            "❌ <b>သင့်ငွေဖြည့်သွင်းမှု ငြင်းပယ်ခံရပါသည်!</b>\n\nပြေစာ မမှန်ကန်ခြင်း သို့မဟုတ် ငွေလွှဲမရောက်ရှိခြင်းကြောင့် ဖြစ်နိုင်ပါသည်။ အသေးစိတ် သိရှိလိုပါက Admin ထံ တိုက်ရိုက် ဆက်သွယ်ပေးပါ။"
        )
        bot.answer_callback_query(call.id, "ငွေဖြည့်လွှာကို ငြင်းပယ်ပြီးပါပြီ")

if __name__ == '__main__':
    print("🚀 StarGrow Telegram Top-up Bot is running on Railway...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
