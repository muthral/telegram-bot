import os
import random
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

chat_aktif = {}
chat_members = {}
game_sessions = {}

jawaban = [
    "iyah",
    "g",
    "gak",
    "mungkin",
    "pasti",
    "100%",
    "impossible",
    "tidak akan",
    "waduh ini sulit, ak nyerah",
    "bisa jadi",
    "kayaknya iya",
    "gatau coba tanya camel",
    "gay",
    "1000000%",
    "37% iya",
    "berdoa saja",
    "omaigot, pertanyaan macam apa ini",
    "omaigot",
    "😱",
    "i hate u",
    "stop asking",
    "bntar, cape.. satu2 guys",
    "iya (btw i love siyc)",
    "ewh",
    "serius nanya ini?",
    "iya dong",
    "gak dong, pake nanya",
    "nyawit ni orang",
    "stoooop",
    "kamu nanya?",
    "km nanyea?",
    "aah ah ahhh..",
    "🤤🤤🤤",
    "hehe, ga",
    "*ngangguk",
    "jangan sekarang",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        pesan = (
            "selamat datang di bot kutil ajaib, katakan \"hidup kutil ajaib!\"\n\n"
            "tanya pertanyaan apapun menggunakan command /apa lalu masukan pertanyaanmu setelah spasi.\n\n"
            "contoh:\n"
            "/apa aku gay?\n\n"
            "terdapat juga command lainnya, cek di /help"
        )
        await update.message.reply_text(pesan)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = (
        "📋 daftar command bot kutil ajaib:\n\n"
        "/apa [pertanyaan] — tanya pertanyaan, bot akan jawab secara random\n"
        "contoh: /apa aku akan lulus ujian?\n\n"
        "/hitung [pertanyaan] — hitung sesuatu, bot kasih angka 0–100\n"
        "contoh: /hitung berapa persen kecocokkan kita?\n\n"
        "/istirahat — bot istirahat sementara (tidak akan jawab /apa)\n\n"
        "/bangun — bangunin bot lagi setelah istirahat\n\n"
        "/tagrandom — tag 1 member random yang pernah aktif di grup\n\n"
        "/help — tampilkan daftar command ini"
    )
    await update.message.reply_text(pesan)

async def track_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return
    user = update.message.from_user
    if user.is_bot:
        return
    chat_id = update.message.chat_id
    if chat_id not in chat_members:
        chat_members[chat_id] = {}
    chat_members[chat_id][user.id] = user

async def tagrandom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    members = chat_members.get(chat_id, {})
    if not members:
        await update.message.reply_text("belum ada member yang terdeteksi, tunggu dulu ada yang chat di sini 😅")
        return
    user = random.choice(list(members.values()))
    if user.username:
        mention = f"@{user.username}"
    else:
        mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    await update.message.reply_text(f"yang terpilih: {mention} 🎯", parse_mode="HTML")

async def hitung(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("masukkan pertanyaannya")
        return

    pertanyaan = " ".join(context.args).lower()
    angka = random.randint(0, 100)

    if "persen" in pertanyaan:
        hasil = f"{angka}%"
    else:
        hasil = str(angka)

    await update.message.reply_text(hasil)

async def bangun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    chat_aktif[chat_id] = True
    await update.message.reply_text("bot sudah bangun, aku siap bekerja!")

async def istirahat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    chat_aktif[chat_id] = False
    await update.message.reply_text("oke aku istirahat dulu, aktifin lagi pake /bangun 😴")

async def apa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not chat_aktif.get(chat_id, True):
        return

    if not context.args:
        await update.message.reply_text("masukkan pertanyaannya")
        return

    pertanyaan = " ".join(context.args).lower()

    if context.args[0].lower() == "kabar":
        await update.message.reply_text("baik")
        return

    responses = []

    if "islam" in pertanyaan or "kristen" in pertanyaan or "buddha" in pertanyaan or "konghucu" in pertanyaan or "hindu" in pertanyaan:
        responses.append("jangan bawa2 agama")
    if "bubar" in pertanyaan:
        responses.append("jangan sebut b word")
    if "prabowo" in pertanyaan:
        responses.append("wowo? i hate that guy")
    if "israel" in pertanyaan:
        responses.append("fuck israel")
    if ("siyc" in pertanyaan or "sik" in pertanyaan) and ("camel" in pertanyaan or "kamel" in pertanyaan):
        responses.append("gtw yang jelas camel dan siyc berjodoh <3")

    if responses:
        hasil = "\n".join(responses)
    else:
        hasil = random.choice(jawaban)

    await update.message.reply_text(hasil)

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("bangun", bangun))
    app.add_handler(CommandHandler("istirahat", istirahat))
    app.add_handler(CommandHandler("apa", apa))
    app.add_handler(CommandHandler("hitung", hitung))
    app.add_handler(CommandHandler("tagrandom", tagrandom))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_member))

    print("Bot is running...")
    app.run_polling()



