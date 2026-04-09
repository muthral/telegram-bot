import os
from collections import deque
from telegram import Update
from telegram.ext import ContextTypes

from db import (
    db_get_wallet, db_set_wallet, db_get_all_wallets,
    db_get_badges, db_set_badges,
    db_get_scores, db_set_score,
    db_get_wallet_by_name,
)

# =====================
# STICKER FILE IDs
# =====================
STICKER_SPY      = "CAACAgUAAxkBAAFGoEtp1J78ieeRSCFdt3ffBbaK5F3hWgAC8h4AAgFzoFaHuFm9FmtkxTsE"
STICKER_DISKUSI  = "CAACAgUAAxkBAAFGoFFp1J-MAghOVIqTYYwRpixqyE9rRwAC6h0AApsHqFaDtRa9ufQrxzsE"
STICKER_VOTE     = "CAACAgUAAxkBAAFGoFNp1J-1aqIVxA_jOG4cnLM5SF07FAAC5R0AApsHqFZswZfoLh6n_DsE"

# =====================
# SHARED STATE (in-memory)
# =====================
chat_members = {}
recent_chatters = {}
game_sessions = {}
chaos_sessions = {}
duel_sessions = {}
duel_dm_pending = {}
spy_sessions = {}
spy_guess_pending = {}

MAX_RECENT = 300
MAX_BADGES = 10

# =====================
# SLOT CONFIG
# =====================
SLOT_EMOJIS = ["🍎", "🍋", "🍊", "🍇", "⭐", "🎯", "🎰", "💎", "🪽"]
DIAMOND = "💎"
SUPER_JACKPOT_EMOJI = "🪽"
SLOT_COST = 5_000
SLOT_WIN_NORMAL = 500_000
SLOT_WIN_DIAMOND = 1_000_000
SLOT_WIN_SUPER = 3_000_000
SLOT_INITIAL = 100_000

# =====================
# SHOP CONFIG
# =====================
SHOP_ITEMS = {
    "💖": 1_000_000,
    "✨": 5_000_000,
    "💎": 10_000_000,
    "🪽": 20_000_000,
    "🔮": 50_000_000,
    "👑": 100_000_000,
}

EXCHANGE_RATES = {
    500: 200_000,
    1000: 500_000,
    2000: 2_000_000,
    3000: 5_000_000,
}

# =====================
# HELPER FUNCTIONS
# =====================

def hitung_poin(jumlah_tebakan: int) -> int:
    if jumlah_tebakan == 1:
        return 100
    elif jumlah_tebakan == 2:
        return 90
    elif jumlah_tebakan == 3:
        return 80
    elif jumlah_tebakan == 4:
        return 70
    elif jumlah_tebakan == 5:
        return 60
    elif jumlah_tebakan <= 8:
        return 50
    else:
        return 25

def get_raw_name(user) -> str:
    return f"@{user.username}" if user.username else user.first_name

async def get_display_name(user) -> str:
    base = get_raw_name(user)
    badges = await db_get_badges(user.id)
    if badges:
        return f"{base} {''.join(badges)}"
    return base

# Untuk kompatibilitas
get_nama = get_display_name

def format_rupiah(jumlah: int) -> str:
    neg = jumlah < 0
    s = f"{abs(jumlah):,}".replace(",", ".")
    return f"-Rp {s},-" if neg else f"Rp {s},-"

async def init_wallet(user):
    uid = user.id
    name = get_raw_name(user)
    data = await db_get_wallet(uid)
    if data is None:
        # Cek placeholder (user_id=0) dengan nama yang sama
        placeholder = await db_get_wallet_by_name(name)
        if placeholder:
            await db_set_wallet(uid, name, placeholder["saldo"])
            badges = await db_get_badges(0)
            if badges:
                await db_set_badges(uid, badges)
                await db_set_badges(0, [])
        else:
            await db_set_wallet(uid, name, SLOT_INITIAL)
    else:
        if data["name"] != name:
            await db_set_wallet(uid, name, data["saldo"])

async def add_score(chat_id, user, points: int):
    uid = user.id
    name = get_raw_name(user)
    scores_dict = await db_get_scores(chat_id)
    current = scores_dict.get(uid, {}).get("score", 0)
    new_score = current + points
    await db_set_score(chat_id, uid, name, new_score)

# Placeholder untuk kompatibilitas (tidak digunakan)
async def save_scores():
    pass

async def load_scores():
    pass

async def send_sticker(chat_id_or_update, sticker_id, context, is_reply=False):
    try:
        if is_reply and hasattr(chat_id_or_update, "message"):
            await chat_id_or_update.message.reply_sticker(sticker_id)
        else:
            await context.bot.send_sticker(chat_id=chat_id_or_update, sticker=sticker_id)
    except Exception:
        pass

# Wrapper untuk akses dari modul lain
async def get_wallet_dict():
    rows = await db_get_all_wallets()
    result = {}
    for r in rows:
        if r["user_id"] != 0:
            result[r["user_id"]] = {"name": r["name"], "saldo": r["saldo"]}
    return result

async def get_scores_dict(chat_id):
    return await db_get_scores(chat_id)
