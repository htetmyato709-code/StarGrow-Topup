import telebot
from telebot import types
from supabase import create_client, Client
import json
import os

# ================= Configuration =================
BOT_TOKEN = "8979642001:AAG3Eanke57GW0XI9Gvo89VhaNLkU0geV24"
ADMIN_CHAT_ID = 8305397892

SUPABASE_URL = "https://emowrxzckktfmlqhkoxk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVtb3dyeHpja2t0Zm1scWhrb3hrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc5NzY0NjAsImV4cCI6MjEwMzU1MjQ2MH0.tNVyZFLk9OZ4Kc0_cPoUKX5unYfCM6JiqG_NamZD1yw"

bot = telebot.TeleBot(BOT_TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Data Persistence Files
USERS_FILE = "bot_users.json"
MAPPINGS_FILE = "user_mappings.json"

def load_data(file_path, default_val):
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default_val
    return default_val

def save_data(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

bot_users = set(load_data(USERS_FILE, []))
user_mappings = load_data(MAPPINGS_FILE, {})  # { "chat_id": "website_username" }

def track_user(chat_id):
    if chat_id not in bot_users:
        bot_users.add(chat_id)
        save_data(USERS_FILE, list(bot_users))

user_states = {}

# ================= Inline Main Menu Buttons =================
def get_main_menu():
    markup = types.InlineKeyboardMarkup()
    btn_deposit = types.InlineKeyboardButton("💳 ငွေဖြည့်မည်", callback_data="menu_deposit")
    btn_change = types.InlineKeyboardButton("⚙️ Username ပြောင်းမည်", callback_data="menu_change_user")
    markup.add(btn_deposit)
    markup.add(btn_change)
    return markup

# User ၏ လက်ကျန်ငွေ Database မှ ဆွဲယူသည့် Helper
def get_user_balance_text(username):
    try:
        res = supabase.table('profiles').select('balance').ilike('username', username).execute()
        if res.data and len(res.data) > 0:
            bal = float(res.data[0].get('balance') or 0)
            return f"{bal:,.0f} Ks"
    except Exception as e:
        print("Balance fetch error:", e)
    return "0 Ks"

# ================= /start Command =================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = str(message.chat.id)
    track_user(message.chat.id)
    
    current_user = user_mappings.get(chat_id)

    # Username မချိတ်ရသေးပါက အရင်တောင်းခံခြင်း
    if not current_user:
        user_states[message.chat.id] = {'step': 'WAITING_INITIAL_USERNAME'}
        bot.send_message(
            message.chat.id,
            "👋 မင်္ဂလာပါခင်ဗျာ!\n\nStarGrow Website တွင် ဖွင့်ထားသော သင်၏ **Username** ကို ရိုက်ထည့်ပေးပါခင်ဗျာ:",
            parse_mode="Markdown"
        )
        return

    # လက်ကျန်ငွေ ဆွဲယူ၍ ကြိုဆိုလွှာ ပြသခြင်း
    bal_text = get_user_balance_text(current_user)
    welcome_text = (
        f"👋 မင်္ဂလာပါ @{current_user}\n\n"
        f"💰 လက်ကျန်ငွေ: {bal_text}\n\n"
        f"အောက်ပါခလုတ်ကိုနှိပ်၍ ငွေဖြည့်သွင်းနိုင်ပါသည် 👇"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu())

# Username ပထမဆုံးအကြိမ် ထည့်သွင်းခြင်း လက်ခံခြင်း
@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get('step') == 'WAITING_INITIAL_USERNAME')
def process_initial_username(message):
    uname = message.text.strip().replace('@', '')
    user_mappings[str(message.chat.id)] = uname
    save_data(MAPPINGS_FILE, user_mappings)
    user_states.pop(message.chat.id, None)
    
    bot.send_message(message.chat.id, f"✅ @{uname} အကောင့်အား အောင်မြင်စွာ ချိတ်ဆက်ပြီးပါပြီ!")
    
    bal_text = get_user_balance_text(uname)
    welcome_text = (
        f"👋 မင်္ဂလာပါ @{uname}\n\n"
        f"💰 လက်ကျန်ငွေ: {bal_text}\n\n"
        f"အောက်ပါခလုတ်ကိုနှိပ်၍ ငွေဖြည့်သွင်းနိုင်ပါသည် 👇"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu())

# ================= ⚙️ Username ပြောင်းမည် (Inline Action) =================
@bot.callback_query_handler(func=lambda call: call.data == "menu_change_user")
def handle_inline_change_username(call):
    bot.answer_callback_query(call.id)
    user_states[call.message.chat.id] = {'step': 'CHANGING_USERNAME'}
    msg = (
        "⚙️ **Username ပြောင်းမည်**\n\n"
        "StarGrow Website တွင် ဖွင့်ထားသော **Username အသစ်** ကို ရိုက်ပို့ပေးပါ:\n"
        "*(မပြောင်းလိုပါက /cancel ဟု ရိုက်ပါ)*"
    )
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get('step') == 'CHANGING_USERNAME')
def process_new_username(message):
    if message.text.startswith('/'):
        return
    new_uname = message.text.strip().replace('@', '')
    user_mappings[str(message.chat.id)] = new_uname
    save_data(MAPPINGS_FILE, user_mappings)
    user_states.pop(message.chat.id, None)

    bot.send_message(message.chat.id, f"✅ @{new_uname} အကောင့်အား အောင်မြင်စွာ ချိတ်ဆက်ပြီးပါပြီ!")

    bal_text = get_user_balance_text(new_uname)
    welcome_text = (
        f"👋 မင်္ဂလာပါ @{new_uname}\n\n"
        f"💰 လက်ကျန်ငွေ: {bal_text}\n\n"
        f"အောက်ပါခလုတ်ကိုနှိပ်၍ ငွေဖြည့်သွင်းနိုင်ပါသည် 👇"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_menu())

# ================= 💳 ငွေဖြည့်မည် (Inline Action) =================
@bot.callback_query_handler(func=lambda call: call.data == "menu_deposit")
def handle_inline_deposit(call):
    bot.answer_callback_query(call.id)
    show_payment_methods(call.message.chat.id)

def show_payment_methods(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌊 WavePay (ရွေးမည်)", callback_data="pay_wave"))
    
    uname = user_mappings.get(str(chat_id), 'user')
    bot.send_message(
        chat_id,
        f"💳 **ငွေပေးချေမှု နည်းလမ်း ရွေးချယ်ပါ**\n\n👤 လက်ရှိ User: **@{uname}**\n\nအောက်ပါ Payment ခလုတ်ကို နှိပ်ပါခင်ဗျာ-",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ================= WavePay ရွေးချယ်ခြင်း -> ပမာဏ အရင်တောင်းခြင်း =================
@bot.callback_query_handler(func=lambda call: call.data == "pay_wave")
def ask_amount(call):
    bot.answer_callback_query(call.id)
    user_states[call.message.chat.id] = {'step': 'WAITING_AMOUNT'}
    
    msg = (
        "💰 **ငွေဖြည့်မည့် ပမာဏ ရိုက်ထည့်ပါ**\n\n"
        "ဖြည့်သွင်းလိုသော ပမာဏအား အောက်တွင် ဂဏန်းသီးသန့် ရိုက်ထည့်ပေးပါခင်ဗျာ။\n\n"
        "⚠️ **အနည်းဆုံး ငွေဖြည့်ပမာဏ:** `1,000` ကျပ်\n"
        "*(ဥပမာ - 1000, 2500, 5000)*"
    )
    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")

# ================= ပမာဏ စစ်ဆေးခြင်း (အနည်းဆုံး ၁,၀၀၀ ကျပ်) -> Phone နံပါတ် ပြသခြင်း =================
@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get('step') == 'WAITING_AMOUNT')
def process_amount_input(message):
    try:
        amount = float(message.text.strip().replace(',', ''))
        
        # ၁,၀၀၀ ကျပ် အနည်းဆုံး စစ်ဆေးခြင်း
        if amount < 1000:
            bot.send_message(
                message.chat.id,
                "⚠️ **ငွေဖြည့်ပမာဏ နည်းလွန်းနေပါသည်!**\n\nအနည်းဆုံး **1,000 ကျပ်** မှစတင်၍ ဖြည့်သွင်းနိုင်ပါသည်။ ကျေးဇူးပြု၍ ၁,၀၀၀ နှင့်အထက် ပြန်လည်ရိုက်ထည့်ပေးပါခင်ဗျာ-",
                parse_mode="Markdown"
            )
            return

        user_states[message.chat.id]['amount'] = amount
        user_states[message.chat.id]['step'] = 'WAITING_SLIP'
        
        formatted_amt = "{:,}".format(int(amount))
        payment_info = (
            f"✅ **ငွေလွှဲရန် အချက်အလက်များ**\n\n"
            f"💵 လွှဲရမည့် ပမာဏ: **{formatted_amt} MMK**\n\n"
            f"🌊 **WavePay နံပါတ်:** `09940391862`\n"
            f"👤 **အမည်:** **Ohn Mar Lwin**\n\n"
            f"⚠️ *(နံပါတ်ကို နှိပ်ပြီး Copy ယူနိုင်ပါသည်)*\n\n"
            f"ငွေလွှဲပြီးပါက ရရှိလာသော **Wave ငွေလွှဲပြေစာ (Slip) Screenshot ဓာတ်ပုံ** ကို ဤနေရာသို့ ပို့ပေးပါခင်ဗျာ။"
        )
        bot.send_message(message.chat.id, payment_info, parse_mode="Markdown")

    except ValueError:
        bot.send_message(message.chat.id, "❌ ပမာဏ မှားယွင်းနေပါသည်။ ဂဏန်းသီးသန့် (ဥပမာ - 1000, 5000) သာ ရိုက်ထည့်ပေးပါခင်ဗျာ။")

# ================= Slip Upload & Admin Notification =================
@bot.message_handler(content_types=['photo'], func=lambda msg: user_states.get(msg.chat.id, {}).get('step') == 'WAITING_SLIP')
def handle_slip_upload(message):
    chat_id = str(message.chat.id)
    username = user_mappings.get(chat_id, 'Unknown')
    amount = user_states[message.chat.id].get('amount', 0)
    formatted_amt = "{:,}".format(int(amount))
    
    photo_id = message.photo[-1].file_id
    
    markup = types.InlineKeyboardMarkup()
    btn_approve = types.InlineKeyboardButton("✅ လက်ခံမည် (Approve)", callback_data=f"app_{username}_{amount}_{message.chat.id}")
    btn_reject = types.InlineKeyboardButton("❌ ငြင်းပယ်မည် (Reject)", callback_data=f"rej_{username}_{amount}_{message.chat.id}")
    markup.row(btn_approve, btn_reject)
    
    admin_caption = (
        "📩 **ငွေဖြည့်သွင်းလွှာ အသစ်ရောက်ရှိပါသည်!**\n\n"
        f"👤 **Username:** `@{username}`\n"
        f"🌊 **Payment:** WavePay (09940391862)\n"
        f"💰 **ပမာဏ:** **{formatted_amt} Ks**\n"
        f"🆔 **Telegram ID:** `{message.chat.id}`"
    )
    
    try:
        bot.send_photo(ADMIN_CHAT_ID, photo_id, caption=admin_caption, reply_markup=markup, parse_mode="Markdown")
        bot.send_message(
            message.chat.id,
            "📩 **ငွေလွှဲပြေစာအား လက်ခံရရှိပါပြီခင်ဗျာ**\n\n"
            "Admin မှ စစ်ဆေးပြီးပါက သင့်အကောင့်ထဲသို့ Balance အလိုအလျောက် ပေါင်းထည့်ပေးပါမည်။ ခေတ္တစောင့်ဆိုင်းပေးပါခင်ဗျာ။"
        )
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Error ဖြစ်ပေါ်သွားပါသည်။ Admin ထံ တိုက်ရိုက် ဆက်သွယ်ပေးပါ။")
    
    user_states.pop(message.chat.id, None)

# ================= Approve / Reject Handlers =================
@bot.callback_query_handler(func=lambda call: call.data.startswith('app_') or call.data.startswith('rej_'))
def handle_admin_decision(call):
    action, username, amount_str, user_chat_id = call.data.split('_')
    amount = float(amount_str)
    formatted_amt = "{:,}".format(int(amount))
    
    if action == "app":
        try:
            # 1. User စစ်ဆေးခြင်း
            res = supabase.table('profiles').select('*').ilike('username', username).execute()
            if not res.data:
                bot.answer_callback_query(call.id, f"User @{username} ကို ရှာမတွေ့ပါ!", show_alert=True)
                return
            
            user = res.data[0]
            current_balance = float(user.get('balance') or 0)
            new_balance = current_balance + amount
            formatted_new_bal = "{:,}".format(int(new_balance))
            
            # 2. Balance ပေါင်းထည့်ခြင်း
            supabase.table('profiles').update({'balance': new_balance}).eq('id', user['id']).execute()
            
            # Admin Message ပြင်ဆင်ခြင်း
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=call.message.caption + f"\n\n✅ **အတည်ပြုပြီးပါပြီ (Approved)**\n💰 ထည့်သွင်းငွေ: +{formatted_amt} Ks\n💳 Balance အသစ်: {formatted_new_bal} Ks",
                reply_markup=None
            )
            bot.answer_callback_query(call.id, "ငွေဖြည့်သွင်းမှု အောင်မြင်ပါသည်!")
            
            # 3. User ထံ သေသပ်လှပစွာ Auto စာပို့ခြင်း
            success_msg = (
                "🎉 **ငွေဖြည့်သွင်းမှု အောင်မြင်ပါသည်!** 🎉\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 **အကောင့်:** `@{username}`\n"
                f"💵 **ဖြည့်သွင်းငွေ:** `+{formatted_amt} MMK`\n"
                f"💳 **လက်ရှိ Balance အသစ်:** `{formatted_new_bal} MMK`\n"
                "🌊 **Payment:** WavePay (Auto Confirmed)\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "StarGrow Boost ဝန်ဆောင်မှုများကို စိတ်ကြိုက် စတင်မှာယူနိုင်ပါပြီခင်ဗျာ။ ကျေးဇူးတင်ရှိပါသည်။ ✨"
            )
            try:
                bot.send_message(user_chat_id, success_msg, parse_mode="Markdown")
            except:
                pass
                
        except Exception as e:
            bot.answer_callback_query(call.id, f"Error: {str(e)}", show_alert=True)
            
    elif action == "rej":
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=call.message.caption + f"\n\n❌ **ငြင်းပယ်လိုက်ပါပြီ (Rejected)**",
            reply_markup=None
        )
        bot.answer_callback_query(call.id, "ငြင်းပယ်လိုက်ပါပြီ!")
        
        # User ထံ ငြင်းပယ်ကြောင်း အကြောင်းကြားစာ
        reject_msg = (
            "⚠️ **ငွေဖြည့်သွင်းမှု ပယ်ဖျက်ခံရပါသည်**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 အကောင့်: `@{username}`\n"
            f"💵 တောင်းဆိုငွေ: `{formatted_amt} MMK`\n\n"
            "ငွေလွှဲပြေစာ အချက်အလက် မကိုက်ညီခြင်း (သို့မဟုတ်) မှားယွင်းနေခြင်းကြောင့် ပယ်ဖျက်လိုက်ပါသည်ခင်ဗျာ။\n"
            "အမှားအယွင်းရှိပါက Admin ထံ ပြန်လည် ဆက်သွယ်ပေးပါခင်ဗျာ။"
        )
        try:
            bot.send_message(user_chat_id, reject_msg, parse_mode="Markdown")
        except:
            pass

# ================= Send Post (Broadcast) Feature =================
@bot.message_handler(commands=['sendpost', 'broadcast'])
def handle_send_post(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return
    
    user_states[message.chat.id] = {'step': 'WAITING_BROADCAST_CONTENT'}
    msg_guide = (
        "📢 **Send Post (အသုံးပြုသူများထံ ကြေညာချက်ပို့ရန်)**\n\n"
        "ပို့လိုသော **စာသား** (သို့မဟုတ်) **ပုံနှင့်အတူ Caption စာသား** ကို ပို့ပေးပါခင်ဗျာ။\n"
        "*(မပို့လိုတော့ပါက /cancel ဟု ရိုက်ပါ)*"
    )
    bot.send_message(message.chat.id, msg_guide, parse_mode="Markdown")

@bot.message_handler(commands=['cancel'])
def handle_cancel(message):
    user_states.pop(message.chat.id, None)
    bot.send_message(message.chat.id, "ပယ်ဖျက်လိုက်ပါပြီ။")

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id, {}).get('step') == 'WAITING_BROADCAST_CONTENT', content_types=['text', 'photo'])
def execute_broadcast(message):
    if message.chat.id != ADMIN_CHAT_ID:
        return
    
    users = list(bot_users)
    total_users = len(users)
    success_count = 0
    fail_count = 0
    
    progress_msg = bot.send_message(ADMIN_CHAT_ID, f"🚀 Post စတင် ပေးပို့နေပါသည်... (စုစုပေါင်း: {total_users} ဦး)")
    
    is_photo = message.content_type == 'photo'
    photo_id = message.photo[-1].file_id if is_photo else None
    caption_text = message.caption if is_photo else message.text
    
    for uid in users:
        try:
            if is_photo:
                bot.send_photo(uid, photo_id, caption=caption_text, parse_mode="Markdown")
            else:
                bot.send_message(uid, caption_text, parse_mode="Markdown")
            success_count += 1
        except Exception:
            fail_count += 1
            
    user_states.pop(message.chat.id, None)
    bot.edit_message_text(
        chat_id=ADMIN_CHAT_ID,
        message_id=progress_msg.message_id,
        text=f"✅ **Post ပို့ဆောင်မှု ပြီးဆုံးပါပြီ!**\n\n📊 အောင်မြင်: {success_count} ဦး\n⚠️ မရောက်ရှိ: {fail_count} ဦး"
    )

# ================= Bot Entry Point =================
if __name__ == '__main__':
    print("StarGrow Bot is online and ready...")
    try:
        # Conflict 409 ကာကွယ်ရန် webhook နှင့် pending updates များကို အရင်ရှင်းခြင်း
        bot.remove_webhook()
    except Exception as e:
        print("Webhook clean error:", e)
        
    bot.infinity_polling(skip_pending=True)
    
