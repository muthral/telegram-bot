import random
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from data import spy_sessions, spy_guess_pending, send_sticker, STICKER_SPY, STICKER_DISKUSI, STICKER_VOTE, get_nama

spy_words = [
    "roti", "mie", "bubur", "rendang", "pempek", "cimol", "sate", "ayam",
    "kucing", "anjing", "serigala", "bunga", "gelas", "piring", "dompet",
    "kasur", "mobil", "rumah", "bantal", "sendok", "meja", "kertas", "dokumen",
    "sekolah", "dokter", "guru", "perawat", "asisten", "celana", "rok",
    "kerudung", "sarung", "tv", "parfum", "charger", "tetikus", "kabel",
    "plastik", "tas", "keyboard", "uang", "bank", "hutang", "ide", "buku",
    "novel", "kamus", "berlian", "cincin", "emas", "kopi", "teh",
    "matcha", "vanila", "cireng", "permen", "jelly", "coklat"
]

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
        "🕵️ <b><u>GAME SPY DIMULAI</u></b>\n"
        "semua pemain akan mendapat pesan rahasia, hanya spy yang tidak mendapatkannya. "
        "Bisakah kalian menebak siapa SPY nya?\n\n"
        "klik /join untuk ikut\n"
        "minimal 3 pemain\n\n"
        "klik /startspy untuk mulai\n\n"
        "👥 pemain:\n"
        "-",
        parse_mode="HTML"
    )

    spy_sessions[chat_id]["msg_id"] = msg.message_id

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

    nama = await get_nama(user)
    await update.message.reply_text(f"{nama} telah mengikuti permainan!")

    text = "🕵️ GAME SPY\n\nklik /join untuk ikut\nminimal 3 pemain\n\nhost klik /startspy untuk mulai\n\n👥 pemain:\n"
    for u in players.values():
        text += f"{await get_nama(u)}\n"

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=spy_sessions[chat_id]["msg_id"],
            text=text
        )
    except Exception:
        pass

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
        text += f"{await get_nama(u)}\n"

    await update.message.reply_text(text)

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
    except Exception:
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
    spy_name = await get_nama(spy_user)

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
        except Exception:
            await context.bot.send_message(
                chat_id,
                f"⚠️ bot tidak bisa DM spy (spy belum pernah chat dengan bot)\n\n"
                f"🎉 warga menang secara default!\n\n"
                f"spy: {spy_name}\n"
                f"kata: {word}"
            )
    else:
        voted_user = players.get(int(target))
        voted_name = await get_nama(voted_user) if voted_user else "?"

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
        except Exception:
            pass

    await send_sticker(update, STICKER_DISKUSI, context, is_reply=True)

    await update.message.reply_text(
        "📨 kata sudah dikirim ke DM masing-masing\n\n"
        "💬 diskusi dimulai!\n"
        "⏱ waktu diskusi 2 menit\n\n"
        "waktunya saling fitnah untuk menebak siapa SPY nya!"
    )

    await asyncio.sleep(60)
    await context.bot.send_message(chat_id, "⏰ tinggal 1 menit lagi!")
    asyncio.create_task(start_discussion(chat_id, context))

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

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in spy_sessions:
        await update.message.reply_text("tidak ada game spy yang aktif")
        return

    if spy_sessions[chat_id].get("vote_started", False):
        await update.message.reply_text("vote sudah dimulai, tidak bisa skip")
        return

    spy_sessions[chat_id]["vote_started"] = True

    await send_sticker(update, STICKER_VOTE, context, is_reply=True)
    await update.message.reply_text(
        "🗳 vote dimulai lebih awal!\n\n"
        "gunakan /vote @username\n\n"
        "⏱ waktu vote 1 menit"
    )

    await asyncio.sleep(60)
    await end_vote(chat_id, context)

async def stopspy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in spy_sessions:
        del spy_sessions[chat_id]

    await update.message.reply_text("game spy dihentikan")
