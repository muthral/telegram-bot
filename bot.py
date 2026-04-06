import os
import random
import logging
import asyncio
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

# =====================
# GAME SPY DATA
# =====================

spy_sessions = {}

spy_words = [
"roti","mie","bubur","rendang","pempek","cimol","sate","ayam",
"kucing","anjing","serigala","bunga","gelas","piring","dompet",
"kasur","mobil","rumah","bantal","sendok","meja","kertas","dokumen",
"sekolah","dokter","guru","perawat","asisten","celana","rok",
"kerudung","sarung","tv","parfum","charger","tetikus","kabel",
"plastik","tas","keyboard","uang","bank","hutang","ide","buku",
"novel","kamus","kertas","berlian","cincin","emas","kopi","teh",
"matcha","vanila","cireng","permen","jelly","coklat"
]

jawaban = [
"iyah","g","gak","mungkin","pasti","100%","impossible","tidak akan",
"waduh ini sulit, ak nyerah","bisa jadi","kayaknya iya","gatau coba tanya camel",
"gay","1000000%","37% iya","berdoa saja","omaigot, pertanyaan macam apa ini",
"omaigot","😱","i hate u","stop asking","bntar, cape.. satu2 guys",
"iya (btw i love siyc)","ewh","serius nanya ini?","iya dong",
"gak lah, pake nanya","nyawit ni orang","stoooop","kamu nanya?",
"km nanyea?","aah ah ahhh..","🤤🤤🤤","hehe, ga","*ngangguk","jangan sekarang",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        pesan = (
            "selamat datang di bot kutil ajaib\n\n"
            "gunakan /help untuk melihat command."
        )
        await update.message.reply_text(pesan)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = (
        "📋 daftar command bot kutil ajaib:\n\n"
        "/apa [pertanyaan]\n"
        "/hitung [pertanyaan]\n"
        "/istirahat - non aktifkan bot\n"
        "/bangun - aktifkan bot kembali\n"
        "/tagrandom - tag satu member secara random\n"
        "/tebakangka - permainan tebak angka\n"
        "/stoptebak\n"
        "/spy - game spy\n"
        "/join - ikut game spy\n"
        "/startspy - mulai game spy\n"
        "/vote @user - vote spy\n"
        "/stopspy\n"
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

    await update.message.reply_text(
        f"yang terpilih: {mention} 🎯",
        parse_mode="HTML"
    )

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
    await update.message.reply_text("bot sudah bangun!")

async def istirahat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    chat_aktif[chat_id] = False
    await update.message.reply_text("bot istirahat 😴")

async def apa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if not chat_aktif.get(chat_id, True):
        return

    if not context.args:
        await update.message.reply_text("masukkan pertanyaannya")
        return

    pertanyaan = " ".join(context.args).lower()

    responses = []

    if "islam" in pertanyaan or "kristen" in pertanyaan or "buddha" in pertanyaan or "hindu" in pertanyaan:
        responses.append("jangan bawa agama")

    if "israel" in pertanyaan:
        responses.append("fuck israel")

    if responses:
        hasil = "\n".join(responses)
    else:
        hasil = random.choice(jawaban)

    await update.message.reply_text(hasil)

# =====================
# GAME TEBAK ANGKA
# =====================

async def tebakangka(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    key = (chat_id, user_id)

    if key in game_sessions:
        await update.message.reply_text("kamu masih bermain")
        return

    angka = random.randint(0, 100)

    game_sessions[key] = {
        "angka": angka,
        "tebakan": 0
    }

    await update.message.reply_text(
        "permainan tebak angka dimulai.\n"
        "masukkan satu angka antara 0 sampai 100!\n"
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

    if not update.message:
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

    await update.message.reply_text(
        f"kamu berhasil menebaknya dalam {jumlah} kali tebakan."
    )

    del game_sessions[key]

# =====================
# GAME SPY
# =====================

async def spy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    spy_sessions[chat_id] = {
        "players": {},
        "started": False,
        "votes": {}
    }

    await update.message.reply_text(
        "🕵️ GAME SPY DIMULAI\n\n"
        "ketik /join untuk ikut.\n"
        "minimal 3 pemain\n\n"
        "host ketik /startspy untuk mulai"
    )

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id
    user = update.message.from_user

    if chat_id not in spy_sessions:
        return

    spy_sessions[chat_id]["players"][user.id] = user

    total = len(spy_sessions[chat_id]["players"])

    await update.message.reply_text(
        f"{user.first_name} bergabung\n"
        f"total pemain: {total}"
    )

async def startspy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    if chat_id not in spy_sessions:
        return

    players = spy_sessions[chat_id]["players"]

    if len(players) < 3:
        await update.message.reply_text("minimal 3 pemain")
        return

    word = random.choice(spy_words)
    spy_player = random.choice(list(players.keys()))

    spy_sessions[chat_id]["spy"] = spy_player
    spy_sessions[chat_id]["word"] = word
    spy_sessions[chat_id]["started"] = True

    for uid, user in players.items():

        try:

            if uid == spy_player:
                await context.bot.send_message(
                    uid,
                    "🕵️ kamu adalah SPY!\n"
                    "coba tebak kata tanpa ketahuan"
                )
            else:
                await context.bot.send_message(
                    uid,
                    f"🕵️ game spy\n\nkatamu adalah:\n\n{word}"
                )

        except:
            pass

    await update.message.reply_text(
        "kata sudah dikirim ke DM\n\n"
        "diskusi dimulai!\n"
        "waktu: 2 menit"
    )

    await asyncio.sleep(120)

    await context.bot.send_message(
        chat_id,
        "⏳ waktu habis!\n\nvote spy:\n/vote @username"
    )

async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    if chat_id not in spy_sessions:
        return

    if not context.args:
        return

    target = context.args[0].replace("@","")

    if target not in spy_sessions[chat_id]["votes"]:
        spy_sessions[chat_id]["votes"][target] = 0

    spy_sessions[chat_id]["votes"][target] += 1

    await update.message.reply_text("vote diterima")

async def stopspy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    if chat_id in spy_sessions:
        del spy_sessions[chat_id]

    await update.message.reply_text("game spy dihentikan")

# =====================

if __name__ == "__main__":

    if not TOKEN:
        raise ValueError("TOKEN belum diset")

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

    # spy
    app.add_handler(CommandHandler("spy", spy))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("startspy", startspy))
    app.add_handler(CommandHandler("vote", vote))
    app.add_handler(CommandHandler("stopspy", stopspy))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, proses_tebakan))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_member))

    print("Bot is running...")
    app.run_polling()
