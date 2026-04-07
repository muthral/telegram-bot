import os
import random
import logging
import asyncio
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

chat_aktif = {}
chat_members = {}
game_sessions = {}
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
        "📋 daftar command bot kutil ajaib\n\n"
        "/apa\n"
        "/hitung\n"
        "/tagrandom\n"
        "/tebakangka\n\n"
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
    if user.is_bot:
        return

    chat_id = update.message.chat_id

    if chat_id not in chat_members:
        chat_members[chat_id] = {}

    chat_members[chat_id][user.id] = user

# =====================
# TAG RANDOM
# =====================

async def tagrandom(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id
    members = chat_members.get(chat_id, {})

    if not members:
        await update.message.reply_text("belum ada member terdeteksi")
        return

    user = random.choice(list(members.values()))

    if user.username:
        mention = f"@{user.username}"
    else:
        mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'

    await update.message.reply_text(
        f"yang terpilih: {mention}",
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

    angka = random.randint(0,100)
    await update.message.reply_text(str(angka))

# =====================
# TEBAK ANGKA
# =====================

async def tebakangka(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    key = (chat_id,user_id)

    if key in game_sessions:
        await update.message.reply_text("kamu masih bermain")
        return

    angka = random.randint(0,100)

    game_sessions[key] = {
        "angka":angka,
        "tebakan":0
    }

    await update.message.reply_text(
        "permainan dimulai\n"
        "tebak angka 0 - 100"
    )

async def stoptebak(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    key = (chat_id,user_id)

    if key in game_sessions:
        del game_sessions[key]

    await update.message.reply_text("game dihentikan")

async def proses_tebakan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    key = (chat_id,user_id)

    if key not in game_sessions:
        return

    text = update.message.text

    if not text.isdigit():
        return

    tebakan = int(text)
    session = game_sessions[key]

    angka = session["angka"]

    session["tebakan"] += 1

    if tebakan > angka:
        await update.message.reply_text("terlalu besar")
        return

    if tebakan < angka:
        await update.message.reply_text("terlalu kecil")
        return

    await update.message.reply_text("benar!")

    del game_sessions[key]

# =====================
# GAME SPY
# =====================

async def spy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.message.chat_id

    spy_sessions[chat_id] = {
        "players":{},
        "votes":{},
        "msg_id":None,
        "spy":None,
        "word":None,
        "vote_started":False,
        "discussion_task":None
    }

    # Send image first
    try:
        with open('images/waktunya_spy.jpg', 'rb') as photo:
            await update.message.reply_photo(photo=InputFile(photo))
    except:
        pass

    # Then send text
    msg = await update.message.reply_text(
        "🕵️ GAME SPY DIMULAI\n\n"
        "ketik /join untuk ikut\n"
        "minimal 3 pemain\n\n"
        "host ketik /startspy untuk mulai\n\n"
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

    # Cek apakah user sudah join sebelumnya
    if user.id in spy_sessions[chat_id]["players"]:
        await update.message.reply_text(f"{user.first_name} sudah bergabung sebelumnya!")
        return

    spy_sessions[chat_id]["players"][user.id] = user

    players = spy_sessions[chat_id]["players"]

    # Kirim notifikasi ke group
    if user.username:
        await update.message.reply_text(f"@{user.username} telah mengikuti permainan!")
    else:
        await update.message.reply_text(f"{user.first_name} telah mengikuti permainan!")

    text = "🕵️ GAME SPY DIMULAI\n\nketik /join untuk ikut\nminimal 3 pemain\n\nhost ketik /startspy untuk mulai\n\n👥 pemain:\n"

    for u in players.values():
        if u.username:
            text += f"@{u.username}\n"
        else:
            text += u.first_name + "\n"

    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=spy_sessions[chat_id]["msg_id"],
        text=text
    )

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
    
    # Send image first
    try:
        with open('images/vote.jpg', 'rb') as photo:
            await context.bot.send_photo(chat_id=chat_id, photo=InputFile(photo))
    except:
        pass
    
    # Then send text
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

async def end_vote(chat_id, context):
    if chat_id not in spy_sessions:
        return
    
    votes = spy_sessions[chat_id]["votes"]
    players = spy_sessions[chat_id]["players"]
    spy_id = spy_sessions[chat_id]["spy"]
    word = spy_sessions[chat_id]["word"]

    if not votes:
        spy_user = players[spy_id]
        name = spy_user.username if spy_user.username else spy_user.first_name

        await context.bot.send_message(
            chat_id,
            f"😈 tidak ada vote\n\n"
            f"SPY menang!\n\n"
            f"spy adalah: {name}\n"
            f"kata: {word}"
        )

        del spy_sessions[chat_id]
        return

    target = max(votes, key=votes.get)
    spy_user = players[spy_id]
    spy_name = spy_user.username if spy_user.username else spy_user.first_name

    if int(target) == spy_id:
        await context.bot.send_message(
            chat_id,
            f"🎉 SPY tertangkap!\n\n"
            f"spy: {spy_name}\n"
            f"kata: {word}\n\n"
            f"warga menang!"
        )
    else:
        await context.bot.send_message(
            chat_id,
            f"😈 spy lolos!\n\n"
            f"spy: {spy_name}\n"
            f"kata: {word}"
        )

    del spy_sessions[chat_id]

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
    spy_sessions[chat_id]["vote_started"] = False

    for uid,user in players.items():
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

    # Send discussion image first
    try:
        with open('images/waktunya_diskusi.jpg', 'rb') as photo:
            await update.message.reply_photo(photo=InputFile(photo))
    except:
        pass
    
    # Then send text
    await update.message.reply_text(
        "📨 kata sudah dikirim ke DM\n\n"
        "💬 diskusi dimulai!\n"
        "⏱ waktu diskusi 2 menit\n\n"
        "cari siapa SPY nya"
    )

    await asyncio.sleep(60)

    await context.bot.send_message(
        chat_id,
        "⏰ tinggal 1 menit lagi!"
    )

    # Start discussion timer
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

    username = context.args[0].replace("@","")

    players = spy_sessions[chat_id]["players"]

    target_id = None

    for uid,user in players.items():
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
    
    # Cancel any pending discussion tasks
    spy_sessions[chat_id]["vote_started"] = True
    
    # Send image first
    try:
        with open('images/vote.jpg', 'rb') as photo:
            await update.message.reply_photo(photo=InputFile(photo))
    except:
        pass
    
    # Then send text
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

    app.add_handler(CommandHandler("tebakangka", tebakangka))
    app.add_handler(CommandHandler("stoptebak", stoptebak))

    app.add_handler(CommandHandler("spy", spy))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("startspy", startspy))
    app.add_handler(CommandHandler("vote", vote))
    app.add_handler(CommandHandler("pemain", pemain))
    app.add_handler(CommandHandler("stopspy", stopspy))
    app.add_handler(CommandHandler("skip", skip))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, proses_tebakan))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_member))

    print("Bot is running...")
    app.run_polling()
