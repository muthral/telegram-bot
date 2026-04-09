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
user_badges = {}  # {user_id: list[str]}   <-- sekarang list, bukan string tunggal

game_sessions = {}    # /angka (solo)   key: (chat_id, user_id)
chaos_sessions = {}   # /angkachaos    key: chat_id
duel_sessions = {}    # /angkaduel     key: chat_id
duel_dm_pending = {}  # user_id -> chat_id

spy_sessions = {}
spy_guess_pending = {}

MAX_RECENT = 300
MAX_BADGES = 10      # batas maksimal badge per pengguna

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

# =====================
# EXCHANGE RATES (skor -> saldo)
# =====================
EXCHANGE_RATES = {
    500: 200_000,
    1000: 500_000,
    2000: 2_000_000,
    3000: 5_000_000,
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
                    # v bisa berupa string (data lama) atau list (data baru)
                    if isinstance(v, str):
                        user_badges[int(k)] = [v]   # konversi ke list
                    elif isinstance(v, list):
                        user_badges[int(k)] = v
        except Exception:
            pass

def save_scores():
    try:
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
    name = get_raw_name(user)   # simpan nama dasar tanpa badge
    if uid not in scores[chat_id]:
        scores[chat_id][uid] = {"name": name, "score": 0}
    scores[chat_id][uid]["score"] += points
    scores[chat_id][uid]["name"] = name
    save_scores()

def get_raw_name(user) -> str:
    """Nama dasar tanpa badge."""
    return f"@{user.username}" if user.username else user.first_name

def get_display_name(user) -> str:
    """Nama dengan semua badge yang dimiliki."""
    base = get_raw_name(user)
    badges = user_badges.get(user.id, [])
    if badges:
        badge_str = "".join(badges)
        return f"{base} {badge_str}"
    return base

# Untuk kompatibilitas dengan kode lama yang memanggil get_nama,
# kita biarkan get_nama = get_display_name agar semua tampilan langsung berbadge.
# Sedangkan penyimpanan data menggunakan get_raw_name.
get_nama = get_display_name

def format_rupiah(jumlah: int) -> str:
    neg = jumlah < 0
    s = f"{abs(jumlah):,}".replace(",", ".")
    return f"-Rp {s},-" if neg else f"Rp {s},-"

def get_saldo(user_id: int) -> int:
    return wallet.get(user_id, {}).get("saldo", SLOT_INITIAL)

def init_wallet(user):
    uid = user.id
    name = get_raw_name(user)   # simpan nama dasar
    if uid not in wallet:
        wallet[uid] = {
            "name": name,
            "saldo": SLOT_INITIAL
        }
    else:
        wallet[uid]["name"] = name

async def send_sticker(chat_id_or_update, sticker_id, context, is_reply=False):
    try:
        if is_reply and hasattr(chat_id_or_update, "message"):
            await chat_id_or_update.message.reply_sticker(sticker_id)
        else:
            await context.bot.send_sticker(chat_id=chat_id_or_update, sticker=sticker_id)
    except Exception:
        pass
