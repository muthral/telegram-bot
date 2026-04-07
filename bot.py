import os
import random
import logging
import asyncio
import time
from collections import deque
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# =====================
# STICKER FILE IDs
# =====================
STICKER_SPY      = "CAACAgUAAxkBAAFGoEtp1J78ieeRSCFdt3ffBbaK5F3hWgAC8h4AAgFzoFaHuFm9FmtkxTsE"
STICKER_DISKUSI  = "CAACAgUAAxkBAAFGoFFp1J-MAghOVIqTYYwRpixqyE9rRwAC6h0AApsHqFaDtRa9ufQrxzsE"
STICKER_VOTE     = "CAACAgUAAxkBAAFGoFNp1J-1aqIVxA_jOG4cnLM5SF07FAAC5R0AApsHqFZswZfoLh6n_DsE"

chat_aktif = {}
chat_members = {}
recent_chatters = {}
game_sessions = {}
spy_sessions = {}

# spy_guess_pending: {spy_user_id: {"chat_id": ..., "word": ..., "spy_name": ...}}
# diisi saat spy tertangkap dan menunggu tebakan kata
spy_guess_pending = {}

MAX_RECENT = 300

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

# =====================
# HELPER: kirim sticker
# =====================

async def send_sticker(chat_id_or_update, sticker_id, context, is_reply=False):
    try:
        if is_reply and hasattr(chat_id_or_update, 'message'):
            await chat_id_or_update.message.reply_sticker(sticker_id)
        else:
            await context.bot.send_sticker(chat_id=chat_id_or_update, sticker=sticker_id)
    except:
        pass

# =====================
# BASIC COMMAND
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        await update.message.reply_text(
            "selamat datang di bot kutil ajaib\n\n"
            "gunakan /help untuk melihat command."
        )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 daftar command bot kutil ajaib\n"
        "/apa [pertanyaan]\n"
        "/hitung [pertanyaan]\n"
        "/tagrandom - pilih satu member secara random\n"
        "/tag7 - tag 7 member secara random\n\n"
        "🎮 TEBAK ANGKA\n"
        "/tebakangka\n"
        "/stoptebak\n\n"
        "🎮 GAME SPY\n"
        "/spy\n"
        "/join\n"
        "/startspy\n"
        "/vote\n"
        "/pemain\n"
        "/stopspy\n"
        "/skip"
    )

# =====================
# MEMBER TRACK
# =====================

async def track_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    if not user or user.is_bot:
        return

    chat_id = update.message.chat_id
    chat_type = update.message.chat.type

    # Jika pesan dari private chat, cek spy guess dulu
    if chat_type == "private":
        await proses_spy_guess(update, context)
        return

    # Simpan ke chat_members (semua yang pernah chat di grup)
    if chat_id not in chat_members:
        chat_members[chat_id] = {}
    chat_members[chat_id][user.id] = user

    # Simpan ke recent_chatters (untuk /tag7)
    if chat_id not in recent_chatters:
        recent_chatters[chat_id] = deque(maxlen=MAX_RECENT)
    recent_chatters[chat_id].append((time.time(), user))

    # Proses tebakan juga di sini
    await proses_tebakan_internal(update, context)

# =====================
# TAG RANDOM
# =====================

async def tagrandom(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id
    members = chat_members.get(chat_id, {})

    if not members:
        await update.message.reply_text("belum ada member terdeteksi. chat dulu biar kedeteksi!")
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

# =====================
# TAG 7
# =====================

async def tag7(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id
    recent = recent_chatters.get(chat_id)

    if not recent:
        await update.message.reply_text("belum cukup member terdeteksi!")
        return

    seen_ids = set()
    kandidat = []

    for ts, user in reversed(list(recent)):
        if user.id in seen_ids:
            continue
        seen_ids.add(user.id)
        kandidat.append(user)

    if len(kandidat) < 7:
        semua = chat_members.get(chat_id, {})
        for uid, user in semua.items():
            if uid not in seen_ids:
                seen_ids.add(uid)
                kandidat.append(user)

    if len(kandidat) == 0:
        await update.message.reply_text("tidak ada member terdeteksi")
        return

    jumlah_tag = min(7, len(kandidat))
    terpilih = random.sample(kandidat, jumlah_tag)

    mentions = []
    for user in terpilih:
        if user.username:
            mentions.append(f"@{user.username}")
        else:
            mentions.append(f'<a href="tg://user?id={user.id}">{user.first_name}</a>')

    hasil = " ".join(mentions)
    await update.message.reply_text(
        f"🎯 {hasil}",
        parse_mode="HTML"
    )

# =====================
# APA
# =====================

async def apa(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        responses.append("jangan sebut B word")
    if ("siyc" in pertanyaan or "sik" in pertanyaan) and ("camel" in pertanyaan or "kamel" in pertanyaan):
        responses.append("gtw yang jelas camel dan siyc berjodoh <3")

    if responses:
        hasil = "\n".join(responses)
    else:
        hasil = random.choice(jawaban)

    await update.message.reply_text(hasil)

# =====================
# HITUNG
# =====================

async def hitung(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("masukkan pertanyaan")
        return

    pertanyaan = " ".join(context.args).lower()
    angka = random.randint(0, 100)

    if "persen" in pertanyaan:
        await update.message.reply_text(f"{angka}%")
    else:
        await update.message.reply_text(str(angka))

# =====================
# TEBAK ANGKA
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
        "permainan dimulai\n"
        "tebak angka 0 - 100"
    )

async def stoptebak(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    key = (chat_id, user_id)

    if key in game_sessions:
        del game_sessions[key]

    await update.message.reply_text("game dihentikan")

async def proses_tebakan_internal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    key = (chat_id, user_id)

    if key not in game_sessions:
        return

    text = update.message.text

    if not text or not text.strip().lstrip('-').isdigit():
        return

    tebakan = int(text.strip())
    session = game_sessions[key]
    angka = session["angka"]

    session["tebakan"] += 1

    if tebakan > angka:
        await update.message.reply_text("terlalu besar")
        return

    if tebakan < angka:
        await update.message.reply_text("terlalu kecil")
        return

    jumlah = session["tebakan"]

    if jumlah == 1:
        pesan = "🤯🤯🤯OMAIGOT?! sekali tebak langsung bener!"
    elif 2 <= jumlah <= 3:
        pesan = "KEREN SEKALI, KAMU LEGEND!"
    elif 4 <= jumlah <= 6:
        pesan = "woww keren 😎"
    elif 7 <= jumlah <= 9:
        pesan = "lumayan keren"
    elif 10 <= jumlah <= 12:
        pesan = "lama banget nebaknya"
    elif 13 <= jumlah <= 17:
        pesan = "bisa main ga sih"
    else:
        pesan = "nyawit ni orang"

    await update.message.reply_text(
        f"kamu berhasil menebaknya dalam {jumlah} kali tebakan.\n\n{pesan}"
    )

    del game_sessions[key]

# =====================
# GAME SPY
# =====================

async def spy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    spy_sessions[chat_id] = {
        "players": {},
        "votes": {},
        "msg_id": None,
        "spy": None,
        "word": None,
        "started": False,
        "vote_started": False,
        "discussion_task": None
    }

    await send_sticker(update, STICKER_SPY, context, is_reply=True)

    msg = await update.message.reply_text(
        "🕵️ GAME SPY DIMULAI\n"
        "semua pemain akan mendapat pesan rahasia, hanya spy yang tidak mendapatkannya. "
        "Bisakah kalian menebak siapa SPY nya?\n\n"
        "klik /join untuk ikut\n"
        "minimal 3 pemain\n\n"
        "klik /startspy untuk mulai\n\n"
        "👥 pemain:\n"
        "-"
    )

    spy_sessions[chat_id]["msg_id"] = msg.message_id

# =====================

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id
    user = update.message.from_user

    if chat_id not in spy_sessions:
        return

    if user.id in spy_sessions[chat_id]["players"]:
        await update.message.reply_text(f"{user.first_name} sudah bergabung sebelumnya!")
        return

    spy_sessions[chat_id]["players"][user.id] = user

    players = spy_sessions[chat_id]["players"]

    if user.username:
        await update.message.reply_text(f"@{user.username} telah mengikuti permainan!")
    else:
        await update.message.reply_text(f"{user.first_name} telah mengikuti permainan!")

    text = "🕵️ GAME SPY DIMULAI\n\nklik /join untuk ikut\nminimal 3 pemain\n\nhost klik /startspy untuk mulai\n\n👥 pemain:\n"

    for u in players.values():
        if u.username:
            text += f"@{u.username}\n"
        else:
            text += u.first_name + "\n"

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=spy_sessions[chat_id]["msg_id"],
            text=text
        )
    except:
        pass

# =====================

async def pemain(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    if chat_id not in spy_sessions:
        await update.message.reply_text("belum ada game")
        return

    players = spy_sessions[chat_id]["players"]

    if not players:
        await update.message.reply_text("belum ada pemain")
        return

    text = "👥 pemain spy:\n\n"

    for u in players.values():
        if u.username:
            text += f"@{u.username}\n"
        else:
            text += u.first_name + "\n"

    await update.message.reply_text(text)

# =====================

async def start_discussion(chat_id, context):
    await asyncio.sleep(120)

    if chat_id not in spy_sessions:
        return

    if spy_sessions[chat_id].get("vote_started", False):
        return

    await send_sticker(chat_id, STICKER_VOTE, context)

    await context.bot.send_message(
        chat_id,
        "🗳 diskusi selesai\n\n"
        "sekarang vote spy\n"
        "gunakan /vote @username\n\n"
        "⏱ waktu vote 1 menit"
    )

    spy_sessions[chat_id]["vote_started"] = True

    await asyncio.sleep(60)

    await end_vote(chat_id, context)

# =====================
# SPY GUESS MECHANIC
# =====================

async def spy_guess_timeout(spy_id, chat_id, context):
    await asyncio.sleep(30)

    if spy_id not in spy_guess_pending:
        return

    data = spy_guess_pending.pop(spy_id)
    spy_name = data["spy_name"]
    word = data["word"]

    try:
        await context.bot.send_message(
            spy_id,
            f"⏰ waktu habis!\n\nkata rahasianya adalah: {word}\n\nwarga menang!"
        )
    except:
        pass

    await context.bot.send_message(
        chat_id,
        f"⏰ spy kehabisan waktu untuk menebak!\n\n"
        f"🎉 warga menang!\n\n"
        f"spy: {spy_name}\n"
        f"kata: {word}"
    )

async def proses_spy_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in spy_guess_pending:
        return

    data = spy_guess_pending.pop(user_id)
    word = data["word"]
    chat_id = data["chat_id"]
    spy_name = data["spy_name"]

    tebakan = update.message.text.strip().lower()

    if tebakan == word.lower():
        await update.message.reply_text(
            f"✅ BENAR! kata rahasianya memang '{word}'\n\n"
            f"kamu menang sebagai SPY! 😈"
        )
        await context.bot.send_message(
            chat_id,
            f"😈 SPY MENANG!\n\n"
            f"{spy_name} berhasil menebak kata rahasianya!\n\n"
            f"kata: {word}"
        )
    else:
        await update.message.reply_text(
            f"❌ salah!\n\nkata rahasianya adalah: {word}\n\nwarga menang!"
        )
        await context.bot.send_message(
            chat_id,
            f"🎉 spy gagal menebak!\n\n"
            f"warga menang!\n\n"
            f"spy: {spy_name}\n"
            f"kata: {word}"
        )

async def end_vote(chat_id, context):
    if chat_id not in spy_sessions:
        return

    votes = spy_sessions[chat_id]["votes"]
    players = spy_sessions[chat_id]["players"]
    spy_id = spy_sessions[chat_id]["spy"]
    word = spy_sessions[chat_id]["word"]

    spy_user = players[spy_id]
    spy_name = spy_user.username if spy_user.username else spy_user.first_name

    del spy_sessions[chat_id]

    if not votes:
        await context.bot.send_message(
            chat_id,
            f"😈 tidak ada yang vote!\n\n"
            f"SPY menang!\n\n"
            f"spy adalah: {spy_name}\n"
            f"kata: {word}"
        )
        return

    target = max(votes, key=votes.get)

    if int(target) == spy_id:
        # Spy tertangkap — beri kesempatan tebak kata
        await context.bot.send_message(
            chat_id,
            f"🎉 SPY tertangkap!\n\n"
            f"spy: {spy_name}\n\n"
            f"tapi spy masih punya satu kesempatan!\n"
            f"spy harus menebak kata rahasia lewat DM bot dalam 30 detik...\n\n"
            f"⏳ menunggu tebakan spy..."
        )

        try:
            await context.bot.send_message(
                spy_id,
                f"kamu tertangkap sebagai SPY! 🕵️\n\n"
                f"tapi kamu masih bisa menang!\n"
                f"tebak kata rahasianya sekarang.\n\n"
                f"⏱ kamu punya 30 detik!\n\n"
                f"ketik tebakan kamu:"
            )
            spy_guess_pending[spy_id] = {
                "chat_id": chat_id,
                "word": word,
                "spy_name": spy_name
            }
            asyncio.create_task(spy_guess_timeout(spy_id, chat_id, context))
        except:
            # Gagal DM spy (belum pernah chat dengan bot)
            await context.bot.send_message(
                chat_id,
                f"⚠️ bot tidak bisa DM spy (spy belum pernah chat dengan bot)\n\n"
                f"🎉 warga menang secara default!\n\n"
                f"spy: {spy_name}\n"
                f"kata: {word}"
            )
    else:
        voted_user = players.get(int(target))
        voted_name = voted_user.username if voted_user and voted_user.username else (voted_user.first_name if voted_user else "?")

        await context.bot.send_message(
            chat_id,
            f"😈 spy lolos! yang di-vote bukan spy!\n\n"
            f"yang divote: {voted_name}\n"
            f"spy asli: {spy_name}\n"
            f"kata: {word}"
        )

async def startspy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    if chat_id not in spy_sessions:
        return

    if spy_sessions[chat_id].get("started", False):
        await update.message.reply_text("⚠️ game spy sudah dimulai sebelumnya!")
        return

    players = spy_sessions[chat_id]["players"]

    if len(players) < 3:
        await update.message.reply_text("minimal 3 pemain")
        return

    word = random.choice(spy_words)
    spy_player = random.choice(list(players.keys()))

    spy_sessions[chat_id]["spy"] = spy_player
    spy_sessions[chat_id]["word"] = word
    spy_sessions[chat_id]["vote_started"] = False
    spy_sessions[chat_id]["started"] = True

    for uid, user in players.items():
        try:
            if uid == spy_player:
                await context.bot.send_message(
                    uid,
                    "🕵️ kamu adalah SPY\n"
                    "coba menebak kata tanpa ketahuan"
                )
            else:
                await context.bot.send_message(
                    uid,
                    f"🕵️ game spy\n\nkatamu:\n{word}"
                )
        except:
            pass

    await send_sticker(update, STICKER_DISKUSI, context, is_reply=True)

    await update.message.reply_text(
        "📨 kata sudah dikirim ke DM masing-masing\n\n"
        "💬 diskusi dimulai!\n"
        "⏱ waktu diskusi 2 menit\n\n"
        "waktunya saling fitnah untuk menebak siapa SPY nya!"
    )

    await asyncio.sleep(60)

    await context.bot.send_message(
        chat_id,
        "⏰ tinggal 1 menit lagi!"
    )

    asyncio.create_task(start_discussion(chat_id, context))

# =====================

async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    if chat_id not in spy_sessions:
        await update.message.reply_text("tidak ada game spy yang aktif")
        return

    if not spy_sessions[chat_id].get("vote_started", False):
        await update.message.reply_text("belum waktunya vote, tunggu diskusi selesai")
        return

    if not context.args:
        await update.message.reply_text("gunakan /vote @username")
        return

    username = context.args[0].replace("@", "")

    players = spy_sessions[chat_id]["players"]

    target_id = None

    for uid, user in players.items():
        if user.username and user.username.lower() == username.lower():
            target_id = uid
            break

    if not target_id:
        await update.message.reply_text("user tidak ditemukan")
        return

    user_id = update.message.from_user.id

    if user_id in spy_sessions[chat_id].get("voted_users", set()):
        await update.message.reply_text("kamu sudah vote sebelumnya")
        return

    if "voted_users" not in spy_sessions[chat_id]:
        spy_sessions[chat_id]["voted_users"] = set()

    spy_sessions[chat_id]["voted_users"].add(user_id)
    votes = spy_sessions[chat_id]["votes"]

    votes[str(target_id)] = votes.get(str(target_id), 0) + 1

    await update.message.reply_text(f"✅ vote untuk @{username} diterima")

# =====================

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    if chat_id not in spy_sessions:
        await update.message.reply_text("tidak ada game spy yang aktif")
        return

    if spy_sessions[chat_id].get("vote_started", False):
        await update.message.reply_text("vote sudah dimulai, tidak bisa skip")
        return

    await update.message.reply_text("⏩ vote dimulai lebih awal!")

    spy_sessions[chat_id]["vote_started"] = True

    await send_sticker(update, STICKER_VOTE, context, is_reply=True)

    await update.message.reply_text(
        "🗳 vote dimulai lebih awal!\n\n"
        "gunakan /vote @username\n\n"
        "⏱ waktu vote 1 menit"
    )

    await asyncio.sleep(60)

    await end_vote(chat_id, context)

# =====================

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

    app.add_handler(CommandHandler("apa", apa))
    app.add_handler(CommandHandler("hitung", hitung))
    app.add_handler(CommandHandler("tagrandom", tagrandom))
    app.add_handler(CommandHandler("tag7", tag7))

    app.add_handler(CommandHandler("tebakangka", tebakangka))
    app.add_handler(CommandHandler("stoptebak", stoptebak))

    app.add_handler(CommandHandler("spy", spy))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("startspy", startspy))
    app.add_handler(CommandHandler("vote", vote))
    app.add_handler(CommandHandler("pemain", pemain))
    app.add_handler(CommandHandler("stopspy", stopspy))
    app.add_handler(CommandHandler("skip", skip))

    # Handler untuk semua pesan teks
    # (track member di grup + spy guess di DM + proses tebakan)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_member))

    print("Bot is running...")
    app.run_polling()
