import random
import time
from collections import deque
from telegram import Update
from telegram.ext import ContextTypes

from data import (
    chat_members, recent_chatters,
    MAX_RECENT, get_nama, format_rupiah, get_raw_name,
    game_sessions, chaos_sessions, duel_sessions, duel_dm_pending,
    spy_guess_pending,
    get_scores_dict
)
from db import db_get_badges

jawaban = [
    "iyah", "g", "gak", "mungkin", "pasti", "100%", "impossible", "tidak akan",
    "waduh ini sulit, ak nyerah", "bisa jadi", "kayaknya iya", "gatau coba tanya camel",
    "gay", "1000000%", "37% iya", "berdoa saja", "omaigot, pertanyaan macam apa ini",
    "omaigot", "😱", "i hate u", "stop asking", "bntar, cape.. satu2 guys",
    "iya (btw i love siyc)", "ewh", "serius nanya ini?", "iya dong",
    "gak lah, pake nanya", "nyawit ni orang", "stoooop", "kamu nanya?",
    "km nanyea?", "aah ah ahhh..", "🤤🤤🤤", "hehe, ga", "*ngangguk", "jangan sekarang",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == "private":
        await update.message.reply_text(
            "selamat datang di bot kutil ajaib\n\n"
            "gunakan /help untuk melihat command."
        )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 <b>DAFTAR COMMAND BOT KUTIL AJAIB</b>\n\n"
        "/apa [pertanyaan]\n"
        "/hitung [pertanyaan]\n"
        "/tagrandom — pilih satu member secara random\n"
        "/tag7 — tag 7 member secara random\n\n"
        "🔢 <b>TEBAK ANGKA</b>\n"
        "/angka — solo, hanya kamu\n"
        "/stoptebak — hentikan game /angka\n"
        "/angkachaos — siapapun bisa ikut nebak\n"
        "/stopchaos — hentikan game chaos\n"
        "/angkaduel — duel 2 pemain, nebak angka lawan\n"
        "/joinduel — join game duel\n"
        "/startduel — mulai game duel\n"
        "/stopduel — hentikan game duel\n"
        "/skor — lihat papan skor grup\n\n"
        "🎰 <b>SLOT MACHINE</b>\n"
        "/slot — putar mesin slot (bayar Rp 5.000)\n"
        "/kekayaan — lihat saldo & kekayaan semua pemain\n\n"
        "🏪 <b>TOKO BADGE</b>\n"
        "/shop — lihat daftar badge & harga\n"
        "/beli [emoji] — beli badge untuk username-mu\n"
        "/tukar [jumlah] — tukar skor menjadi saldo\n\n"
        "🎮 <b>GAME SPY</b>\n"
        "/spy\n"
        "/join\n"
        "/startspy\n"
        "/vote\n"
        "/pemain\n"
        "/stopspy\n"
        "/skip",
        parse_mode="HTML"
    )

async def apa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("masukkan pertanyaannya")
        return

    pertanyaan = " ".join(context.args).lower()

    if context.args[0].lower() == "kabar":
        await update.message.reply_text("baik")
        return

    responses = []

    if any(w in pertanyaan for w in ["islam", "kristen", "buddha", "konghucu", "hindu"]):
        responses.append("jangan bawa2 agama")
    if "bubar" in pertanyaan:
        responses.append("jangan sebut B word")
    if ("siyc" in pertanyaan or "sik" in pertanyaan) and ("camel" in pertanyaan or "kamel" in pertanyaan):
        responses.append("gtw yang jelas camel dan siyc berjodoh <3")

    hasil = "\n".join(responses) if responses else random.choice(jawaban)
    await update.message.reply_text(hasil)

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

async def tagrandom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    members = chat_members.get(chat_id, {})

    if not members:
        await update.message.reply_text("belum ada member terdeteksi. chat dulu biar kedeteksi!")
        return

    user = random.choice(list(members.values()))
    mention = f"@{user.username}" if user.username else f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    await update.message.reply_text(f"yang terpilih: {mention} 🎯", parse_mode="HTML")

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
        for uid, user in chat_members.get(chat_id, {}).items():
            if uid not in seen_ids:
                seen_ids.add(uid)
                kandidat.append(user)

    if not kandidat:
        await update.message.reply_text("tidak ada member terdeteksi")
        return

    terpilih = random.sample(kandidat, min(7, len(kandidat)))
    mentions = []
    for user in terpilih:
        if user.username:
            mentions.append(f"@{user.username}")
        else:
            mentions.append(f'<a href="tg://user?id={user.id}">{user.first_name}</a>')

    await update.message.reply_text(f"🎯 {', '.join(mentions)}", parse_mode="HTML")

async def skor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    data = await get_scores_dict(chat_id)

    if not data:
        await update.message.reply_text("belum ada yang main atau belum ada yang menang")
        return

    sorted_scores = sorted(data.items(), key=lambda x: x[1]["score"], reverse=True)
    text = "🏆 <b>PAPAN SKOR GRUP</b>\n\n"
    for i, (uid, info) in enumerate(sorted_scores, 1):
        badges = await db_get_badges(uid)
        raw_name = info["name"]
        display_name = f"{raw_name} {''.join(badges)}" if badges else raw_name
        text += f"{i}. {display_name} — {info['score']} poin\n"

    await update.message.reply_text(text, parse_mode="HTML")

# =====================
# TRACK MEMBER (message handler)
# =====================

async def track_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    if not user or user.is_bot:
        return

    chat_type = update.message.chat.type

    if chat_type == "private":
        from game_spy import proses_spy_guess
        from game_tebak import proses_duel_dm
        await proses_spy_guess(update, context)
        await proses_duel_dm(update, context)
        return

    chat_id = update.message.chat_id

    if chat_id not in chat_members:
        chat_members[chat_id] = {}
    chat_members[chat_id][user.id] = user

    if chat_id not in recent_chatters:
        recent_chatters[chat_id] = deque(maxlen=MAX_RECENT)
    recent_chatters[chat_id].append((time.time(), user))

    from game_tebak import proses_tebakan_internal, proses_chaos_guess, proses_duel_guess
    await proses_tebakan_internal(update, context)
    await proses_chaos_guess(update, context)
    await proses_duel_guess(update, context)
