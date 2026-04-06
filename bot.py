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
    "gak lah, pake nanya",
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
        "/apa [pertanyaan]\n"
        "/hitung [pertanyaan]\n"
        "/istirahat\n"
        "/bangun\n"
        "/tagrandom\n"
        "/tebakangka\n"
        "/stoptebak\n"
        "/help"
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
        await update.message.reply_text("belum ada member yang terdeteksi 😅")
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
    await update.message.reply_text("oke aku istirahat dulu 😴")

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

# =========================
# GAME TEBAK ANGKA
# =========================

async def tebakangka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    key = (chat_id, user_id)

    if key in game_sessions:
        await update.message.reply_text("kamu masih punya game yang belum selesai")
        return

    angka = random.randint(0, 100)

    game_sessions[key] = {
        "angka": angka,
        "tebakan": 0
    }

    await update.message.reply_text(
        "permainan tebak angka dimulai.\n"
        "masukkan satu angka antara 0 sampai 100!\n"
        "(reply pesan ini)"
    )

async def stoptebak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    key = (chat_id, user_id)

    if key not in game_sessions:
        await update.message.reply_text("kamu tidak sedang bermain")
        return

    del game_sessions[key]
    await update.message.reply_text("game dihentikan")

async def proses_tebakan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    key = (chat_id, user_id)

    if key not in game_sessions:
        return

    text = update.message.text.strip()

    if not text.isdigit():
        return

    tebakan = int(text)

    if tebakan < 0 or tebakan > 100:
        return

    session = game_sessions[key]
    angka = session["angka"]

    session["tebakan"] += 1
    jumlah = session["tebakan"]

    if tebakan > angka:
        await update.message.reply_text("angkamu terlalu besar")
        return

    if tebakan < angka:
        await update.message.reply_text("angkamu terlalu kecil")
        return

    if jumlah == 1:
        pesan = "🤯🤯🤯OMAIGOT?! sekali tebak langsung bener, fiks cenanyang!"
    elif 2 <= jumlah <= 3:
        pesan = "KEREN SEKALI, KAMU LEGEND!"
    elif 4 <= jumlah <= 5:
        pesan = "woww keren 😎"
    elif 6 <= jumlah <= 7:
        pesan = "lumayan... coba lagi?"
    elif 8 <= jumlah <= 10:
        pesan = "aowkwkwk lama bgt nebaknya"
    elif 11 <= jumlah <= 15:
        pesan = "bisa main ga sih"
    else:
        pesan = "nyawit ni orang"

    await update.message.reply_text(
        f"kamu berhasil menebaknya dalam {jumlah} kali tebakan.\n\n{pesan}"
    )

    del game_sessions[key]

# =========================

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
    app.add_handler(CommandHandler("tebakangka", tebakangka))
    app.add_handler(CommandHandler("stoptebak", stoptebak))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_member))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, proses_tebakan))

    print("Bot is running...")
    app.run_polling()
