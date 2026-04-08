import random
from telegram import Update
from telegram.ext import ContextTypes

from data import (
    game_sessions, chaos_sessions, duel_sessions, duel_dm_pending,
    add_score, hitung_poin, get_nama
)

# =====================
# /angka (SOLO)
# =====================

async def angka(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    key = (chat_id, user_id)

    if key in game_sessions:
        await update.message.reply_text("kamu masih bermain! selesaikan dulu atau /stoptebak")
        return

    target = random.randint(0, 100)
    game_sessions[key] = {"angka": target, "tebakan": 0}

    await update.message.reply_text(
        "🎯 <b>TEBAK ANGKA DIMULAI!</b>\n\n"
        "tebak angka antara 0 - 100\n"
        "langsung ketik angkanya!",
        parse_mode="HTML"
    )

async def stoptebak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    key = (chat_id, user_id)

    if key in game_sessions:
        target = game_sessions[key]["angka"]
        del game_sessions[key]
        await update.message.reply_text(f"game dihentikan. angkanya adalah {target}")
    else:
        await update.message.reply_text("kamu tidak sedang bermain")

async def proses_tebakan_internal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id
    key = (chat_id, user_id)

    if key not in game_sessions:
        return

    text = update.message.text
    if not text or not text.strip().lstrip("-").isdigit():
        return

    tebakan = int(text.strip())
    session = game_sessions[key]
    target = session["angka"]
    session["tebakan"] += 1

    if tebakan > target:
        await update.message.reply_text("⬇️ terlalu besar")
        return
    if tebakan < target:
        await update.message.reply_text("⬆️ terlalu kecil")
        return

    jumlah = session["tebakan"]
    poin = hitung_poin(jumlah)
    del game_sessions[key]
    add_score(chat_id, update.message.from_user, poin)

    if jumlah == 1:
        pesan = "🤯🤯🤯 OMAIGOT?! SEKALI TEBAK LANGSUNG BENER!!"
    elif jumlah == 2:
        pesan = "🔥 WOW DUA KALI! LUAR BIASA!"
    elif jumlah == 3:
        pesan = "🔥 KEREN SEKALI, KAMU LEGEND!"
    elif jumlah <= 5:
        pesan = "😎 woww keren banget"
    elif jumlah <= 8:
        pesan = "👍 lumayan keren"
    elif jumlah <= 12:
        pesan = "😅 lama banget nebaknya"
    else:
        pesan = "💀 nyawit ni orang"

    await update.message.reply_text(
        f"{pesan}\n\n"
        f"kamu berhasil menebak dalam <b>{jumlah}x</b> tebakan!\n\n"
        f"🏅 +{poin} poin!",
        parse_mode="HTML"
    )

# =====================
# /angkachaos
# =====================

async def angkachaos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in chaos_sessions:
        await update.message.reply_text("🌀 game chaos sudah berjalan!")
        return

    target = random.randint(0, 100)
    chaos_sessions[chat_id] = {"angka": target, "tebakan_per_user": {}}

    await update.message.reply_text(
        "🌀 <b>ANGKA CHAOS DIMULAI!</b>\n\n"
        "siapapun boleh nebak!\n"
        "tebak angka 0 - 100\n\n"
        "langsung ketik angkanya aja!",
        parse_mode="HTML"
    )

async def stopchaos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in chaos_sessions:
        target = chaos_sessions[chat_id]["angka"]
        del chaos_sessions[chat_id]
        await update.message.reply_text(f"game chaos dihentikan. angkanya adalah {target}")
    else:
        await update.message.reply_text("tidak ada game chaos yang berjalan")

async def proses_chaos_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in chaos_sessions:
        return

    text = update.message.text
    if not text or not text.strip().lstrip("-").isdigit():
        return

    tebakan = int(text.strip())
    session = chaos_sessions[chat_id]
    target = session["angka"]
    user = update.message.from_user
    uid = user.id
    nama = get_nama(user)

    session["tebakan_per_user"][uid] = session["tebakan_per_user"].get(uid, 0) + 1

    if tebakan > target:
        await update.message.reply_text(f"⬇️ {nama}: terlalu besar")
        return
    if tebakan < target:
        await update.message.reply_text(f"⬆️ {nama}: terlalu kecil")
        return

    jumlah = session["tebakan_per_user"][uid]
    poin = hitung_poin(jumlah)
    del chaos_sessions[chat_id]
    add_score(chat_id, user, poin)

    await update.message.reply_text(
        f"🎉 <b>{nama}</b> berhasil menebak angka <b>{target}</b>!\n\n"
        f"ditebak dalam <b>{jumlah}x</b> tebakan\n\n"
        f"🏅 +{poin} poin!",
        parse_mode="HTML"
    )

# =====================
# /angkaduel
# =====================

async def angkaduel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in duel_sessions:
        await update.message.reply_text("⚔️ sudah ada game duel, tunggu selesai dulu atau /stopduel")
        return

    duel_sessions[chat_id] = {
        "players": [],
        "player_objs": {},
        "numbers": {},
        "numbers_received": set(),
        "tebakan_per_player": {},
        "turn": 0,
        "started": False
    }

    await update.message.reply_text(
        "⚔️ <b>ANGKA DUEL!</b>\n\n"
        "game untuk 2 pemain saja!\n"
        "ketik /joinduel untuk ikut\n\n"
        "setelah 2 orang join, host ketik /startduel",
        parse_mode="HTML"
    )

async def joinduel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    user = update.message.from_user

    if chat_id not in duel_sessions:
        await update.message.reply_text("belum ada game duel. ketik /angkaduel dulu")
        return

    session = duel_sessions[chat_id]

    if session["started"]:
        await update.message.reply_text("game sudah dimulai, tidak bisa join")
        return

    if user.id in session["player_objs"]:
        await update.message.reply_text("kamu sudah join!")
        return

    if len(session["players"]) >= 2:
        await update.message.reply_text("duel hanya untuk 2 pemain, sudah penuh!")
        return

    session["players"].append(user.id)
    session["player_objs"][user.id] = user
    session["tebakan_per_player"][user.id] = 0

    nama = get_nama(user)
    jumlah = len(session["players"])

    if jumlah == 1:
        await update.message.reply_text(f"✅ {nama} join! menunggu 1 pemain lagi...")
    else:
        await update.message.reply_text(
            f"✅ {nama} join!\n\n"
            f"👥 sudah 2 pemain! host ketik /startduel untuk mulai"
        )

async def startduel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in duel_sessions:
        await update.message.reply_text("belum ada game duel")
        return

    session = duel_sessions[chat_id]

    if session["started"]:
        await update.message.reply_text("game sudah dimulai")
        return

    if len(session["players"]) < 2:
        await update.message.reply_text("⚔️ duel butuh tepat 2 pemain!")
        return

    session["started"] = True
    session["turn"] = 0

    player_a = session["player_objs"][session["players"][0]]
    player_b = session["player_objs"][session["players"][1]]
    nama_a = get_nama(player_a)
    nama_b = get_nama(player_b)

    await update.message.reply_text(
        f"⚔️ <b>DUEL DIMULAI!</b>\n\n"
        f"👤 <b>{nama_a}</b>  VS  👤 <b>{nama_b}</b>\n\n"
        f"📨 bot sudah DM kalian berdua!\n"
        f"silakan masukkan angka rahasiamu via DM bot.\n\n"
        f"game akan mulai setelah keduanya memasukkan angka 🎯",
        parse_mode="HTML"
    )

    for uid in session["players"]:
        user_obj = session["player_objs"][uid]
        nama = get_nama(user_obj)
        try:
            await context.bot.send_message(
                uid,
                f"⚔️ <b>ANGKA DUEL</b>\n\n"
                f"halo {nama}! 👋\n\n"
                f"masukkan angka rahasiamu:\n"
                f"🔢 <b>range: 1 - 100</b>\n\n"
                f"angkamu akan ditebak oleh lawanmu!\n"
                f"pilih dengan bijak 😏",
                parse_mode="HTML"
            )
            duel_dm_pending[uid] = chat_id
        except Exception:
            await context.bot.send_message(
                chat_id,
                f"⚠️ bot tidak bisa DM {get_nama(user_obj)}!\n"
                f"pastikan kamu sudah pernah chat dengan bot dulu ya."
            )

async def stopduel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in duel_sessions:
        for uid in duel_sessions[chat_id].get("players", []):
            duel_dm_pending.pop(uid, None)
        del duel_sessions[chat_id]
        await update.message.reply_text("game duel dihentikan")
    else:
        await update.message.reply_text("tidak ada game duel yang berjalan")

async def proses_duel_dm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in duel_dm_pending:
        return

    text = update.message.text
    if not text or not text.strip().lstrip("-").isdigit():
        await update.message.reply_text("tolong masukkan angka saja (1-100)")
        return

    angka_input = int(text.strip())

    if not (1 <= angka_input <= 100):
        await update.message.reply_text("⚠️ angka harus antara 1 - 100!")
        return

    chat_id = duel_dm_pending.pop(user_id)

    if chat_id not in duel_sessions:
        await update.message.reply_text("sesi duel sudah tidak ada")
        return

    session = duel_sessions[chat_id]
    session["numbers"][user_id] = angka_input

    await update.message.reply_text(
        f"✅ angkamu (<b>{angka_input}</b>) sudah tersimpan!\n\n"
        f"kembali ke grup dan tunggu giliran ya 😊",
        parse_mode="HTML"
    )

    session["numbers_received"].add(user_id)

    if len(session["numbers_received"]) == 2:
        player_a_id = session["players"][0]
        player_b_id = session["players"][1]
        nama_a = get_nama(session["player_objs"][player_a_id])
        nama_b = get_nama(session["player_objs"][player_b_id])

        await context.bot.send_message(
            chat_id,
            f"🎯 <b>KEDUA PEMAIN SUDAH SIAP!</b>\n\n"
            f"⚔️ <b>{nama_a}</b> VS <b>{nama_b}</b>\n\n"
            f"📌 aturan:\n"
            f"• {nama_a} menebak angka {nama_b}\n"
            f"• {nama_b} menebak angka {nama_a}\n"
            f"• siapa duluan yang benar, menang!\n\n"
            f"giliran pertama: <b>{nama_a}</b> 🎲",
            parse_mode="HTML"
        )

async def proses_duel_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id not in duel_sessions:
        return

    session = duel_sessions[chat_id]

    if not session["started"]:
        return

    if len(session["numbers_received"]) < 2:
        return

    text = update.message.text
    if not text or not text.strip().lstrip("-").isdigit():
        return

    user = update.message.from_user
    user_id = user.id
    players = session["players"]

    current_turn_id = players[session["turn"] % 2]
    if user_id != current_turn_id:
        return

    tebakan = int(text.strip())
    lawan_id = players[(session["turn"] + 1) % 2]
    target = session["numbers"][lawan_id]
    nama = get_nama(user)
    nama_lawan = get_nama(session["player_objs"][lawan_id])

    session["tebakan_per_player"][user_id] = session["tebakan_per_player"].get(user_id, 0) + 1

    if tebakan > target:
        await update.message.reply_text(f"⬇️ terlalu besar, {nama}!", reply_to_message_id=update.message.message_id)
    elif tebakan < target:
        await update.message.reply_text(f"⬆️ terlalu kecil, {nama}!", reply_to_message_id=update.message.message_id)
    else:
        jumlah_tebak = session["tebakan_per_player"][user_id]
        del duel_sessions[chat_id]
        add_score(chat_id, user, 60)

        await update.message.reply_text(
            f"🏆 <b>{nama} MENANG DUEL!</b>\n\n"
            f"angka rahasia {nama_lawan} memang <b>{target}</b>!\n\n"
            f"ditebak dalam <b>{jumlah_tebak}x</b> giliran\n\n"
            f"🏅 +60 poin!",
            parse_mode="HTML"
        )
        return

    session["turn"] += 1
    next_id = players[session["turn"] % 2]
    next_player = session["player_objs"][next_id]
    next_nama = get_nama(next_player)

    await context.bot.send_message(
        chat_id,
        f"🎲 giliran: <b>{next_nama}</b>",
        parse_mode="HTML"
    )
