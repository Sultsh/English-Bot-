import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# ======================= CONFIG =======================
BOT_TOKEN = "8538557025:AAHxyGoWwPnjnMIXzwngx8_CZQMBz9yM0Eg"
ADMIN_IDS = [6059547931]  # Admin ID lar ro'yxati

# ======================= VOCAB =======================
vocab = {
    "1": {
        "afraid": "qo'rqmoq",
        "agree": "rozi bo'lmoq",
        "angry": "jahldor",
        "arrive": "yetib kelmoq",
        "attack": "hujum qilmoq",
        "bottom": "tagi osti",
        "clever": "aqilli",
        "cruel": "shafqatsiz",
        "finally": "nihoyat",
        "hide": "yashirmoq",
        "hunt": "ovlamoq",
        "lot": "ko'p",
        "middle": "o'rta",
        "moment": "lahza",
        "pleased": "mamnun",
        "promise": "va'da bermoq",
        "reply": "javob bermoq",
        "safe": "xavfsiz",
        "trick": "hiyla",
        "well": "yaxshi"
    },
    # Shu tarzda 2–30 unitlarni qo‘shing...
}

# ======================= LOGGING =======================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ======================= DATA =======================
active_tests = {}  # {chat_id: {"unit":7, "questions":[...], "index":0, "scores":{user_id:score}}}

# ======================= HELPERS =======================
def generate_question(unit_data):
    word, meaning = random.choice(list(unit_data.items()))
    correct = meaning
    wrong_options = list(unit_data.values())
    wrong_options.remove(correct)
    wrongs = random.sample(wrong_options, 3)
    options = wrongs + [correct]
    random.shuffle(options)
    return word, correct, options

def get_keyboard(options):
    keyboard = []
    for opt in options:
        keyboard.append([InlineKeyboardButton(opt, callback_data=opt)])
    return InlineKeyboardMarkup(keyboard)

# ======================= COMMANDS =======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "😁 Salom! Men @SULTSH_YT tomonidan yaratilgan Lug‘at Bot man.\n"
        "Menda 30 ta unit bor!\n"
        "Meni guruhga qo‘shing va admin qiling — shunda testlar ishlaydi 🚀"
    )

async def unit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # faqat adminlar start qilishi mumkin
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Faqat admin test boshlashi mumkin!")
        return

    if not context.args:
        await update.message.reply_text("Unit raqamini kiriting. Misol: /unit7")
        return

    unit_num = context.args[0]
    if unit_num not in vocab:
        await update.message.reply_text(f"Unit {unit_num} mavjud emas!")
        return

    unit_data = vocab[unit_num]
    questions = []
    for _ in range(20):
        word, correct, options = generate_question(unit_data)
        questions.append({"word": word, "correct": correct, "options": options})

    active_tests[chat_id] = {
        "unit": unit_num,
        "questions": questions,
        "index": 0,
        "scores": {}
    }

    await update.message.reply_text(
        f"🎲 '4000 Essential English Words — Unit {unit_num}' testiga tayyorlaning!\n"
        "🖊 20 ta savol\n"
        "⏱ Har bir savol uchun 10 soniya\n\n"
        "[🚀 Boshlash]"
    )

# ======================= QUESTIONS =======================
async def send_question(chat_id, context: ContextTypes.DEFAULT_TYPE):
    test = active_tests.get(chat_id)
    if not test:
        return
    idx = test["index"]
    if idx >= len(test["questions"]):
        # Test yakunlandi
        scores = test["scores"]
        leaderboard = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        msg = f"🏁 Unit {test['unit']} testi yakunlandi!\n20 ta savol berildi.\n\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, (user, score) in enumerate(leaderboard[:3]):
            msg += f"{medals[i] if i<3 else ''} {user} – {score}\n"
        await context.bot.send_message(chat_id, msg)
        active_tests.pop(chat_id)
        return

    question = test["questions"][idx]
    keyboard = get_keyboard(question["options"])
    await context.bot.send_message(chat_id, f"❓ {question['word']} so‘zining ma’nosini toping:", reply_markup=keyboard)

# ======================= CALLBACK =======================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    test = active_tests.get(chat_id)
    if not test:
        await query.answer()
        return

    idx = test["index"]
    question = test["questions"][idx]

    if user_id in question:
        await query.answer("Siz allaqachon javob berdingiz!")
        return

    selected = query.data
    correct = question["correct"]

    # Score update
    if user_id not in test["scores"]:
        test["scores"][user_id] = 0
    if selected == correct:
        test["scores"][user_id] += 1
        await query.answer("✅ To‘g‘ri!")
    else:
        await query.answer("❌ Noto‘g‘ri!")

    # Disable buttons
    await query.edit_message_reply_markup(reply_markup=None)

    # Keyingi savol
    test["index"] += 1
    await send_question(chat_id, context)

# ======================= MAIN =======================
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("unit", unit_command))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot ishga tushdi...")
    app.run_webhook(
        listen="0.0.0.0",
        port=8080,
        url_path=BOT_TOKEN,
        webhook_url=f"https://<YOUR-RAILWAY-APP-NAME>.up.railway.app/{BOT_TOKEN}"
    )