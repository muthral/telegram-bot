import json
import os
from collections import deque

# =====================
# STICKER FILE IDs
# =====================
STICKER_SPY      = "CAACAgUAAxkBAAFGoEtp1J78ieeRSCFdt3ffBbaK5F3hWgAC8h4AAgFzoFaHuFm9FmtkxTsE"
STICKER_DISKUSI  = "CAACAgUAAxkBAAFGoFFp1J-MAghOVIqTYYwRpixqyE9rRwAC6h0AApsHqFaDtRa9ufQrxzsE"
STICKER_VOTE     = "CAACAgUAAxkBAAFGoFNp1J-1aqIVxA_jOG4cnLM5SF07FAAC5R0AApsHqFZswZfoLh6n_DsE"

# =====================
# SHARED STATE
# =====================
chat_members = {}
recent_chatters = {}
scores = {}       # {chat_id: {user_id: {"name": str, "score": int}}}
wallet = {}       # {user_id: {"name": str, "saldo": int}}
user_badges = {}  # {user_id: str}  e.g. {123: "💖"}

game_sessions = {}    # /angka (solo)   key: (chat_id, user_id)
chaos_sessions = {}   # /angkachaos    key: chat_id
duel_sessions = {}    # /angkaduel     key: chat_id
duel_dm_pending = {}  # user_id -> chat_id

spy_sessions = {}
spy_guess_pending = {}

MAX_RECENT = 300

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
}

# =====================
# PERSISTENCE
# =====================
DATA_DIR = os.path.dirname(__file__)
WALLET_FILE = os.path.join(DATA_DIR, "wallet_data.json")
BADGES_FILE = os.path.join(DATA_DIR, "badges_data.json")
SCORES_FILE = os.path.join(DATA_DIR, "scores_data.json")

def save_wallet():
    try:
        with open(WALLET_FILE, "w") as f:
            json.dump({str(k): v for k, v in wallet.items()}, f)
    except Exception:
        pass

def load_wallet():
    if os.path.exists(WALLET_FILE):
        try:
            with open(WALLET_FILE) as f:
                data = json.load(f)
                for k, v in data.items():
                    wallet[int(k)] = v
        except Exception:
            pass

def save_badges():
    try:
        with open(BADGES_FILE, "w") as f:
            json.dump({str(k): v for k, v in user_badges.items()}, f)
    except Exception:
        pass

def load_badges():
    if os.path.exists(BADGES_FILE):
        try:
            with open(BADGES_FILE) as f:
                data = json.load(f)
                for k, v in data.items():
                    user_badges[int(k)] = v
        except Exception:
            pass

def save_scores():
    try:
        # Ubah key chat_id menjadi string untuk JSON
        data_to_save = {}
        for chat_id, users in scores.items():
            data_to_save[str(chat_id)] = {}
            for uid, info in users.items():
                data_to_save[str(chat_id)][str(uid)] = info
        with open(SCORES_FILE, "w") as f:
            json.dump(data_to_save, f)
    except Exception:
        pass

def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE) as f:
                data = json.load(f)
                for chat_id_str, users in data.items():
                    chat_id = int(chat_id_str)
                    scores[chat_id] = {}
                    for uid_str, info in users.items():
                        scores[chat_id][int(uid_str)] = info
        except Exception:
            pass

load_wallet()
load_badges()
load_scores()

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

def add_score(chat_id, user, points: int):
    if chat_id not in scores:
        scores[chat_id] = {}
    uid = user.id
    name = get_nama(user)
    if uid not in scores[chat_id]:
        scores[chat_id][uid] = {"name": name, "score": 0}
    scores[chat_id][uid]["score"] += points
    scores[chat_id][uid]["name"] = name
    save_scores()  # Simpan setiap kali skor berubah

def get_nama(user) -> str:
    base = f"@{user.username}" if user.username else user.first_name
    badge = user_badges.get(user.id, "")
    return f"{base} {badge}" if badge else base

def format_rupiah(jumlah: int) -> str:
    neg = jumlah < 0
    s = f"{abs(jumlah):,}".replace(",", ".")
    return f"-Rp {s},-" if neg else f"Rp {s},-"

def get_saldo(user_id: int) -> int:
    return wallet.get(user_id, {}).get("saldo", SLOT_INITIAL)

def init_wallet(user):
    uid = user.id
    if uid not in wallet:
        wallet[uid] = {
            "name": get_nama(user),
            "saldo": SLOT_INITIAL
        }
    else:
        wallet[uid]["name"] = get_nama(user)

async def send_sticker(chat_id_or_update, sticker_id, context, is_reply=False):
    try:
        if is_reply and hasattr(chat_id_or_update, "message"):
            await chat_id_or_update.message.reply_sticker(sticker_id)
        else:
            await context.bot.send_sticker(chat_id=chat_id_or_update, sticker=sticker_id)
    except Exception:
        pass
