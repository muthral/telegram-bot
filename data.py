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

game_sessions = {}    # /angka (solo)   key: (chat_id, user_id)
chaos_sessions = {}   # /angkachaos    key: chat_id
duel_sessions = {}    # /angkaduel     key: chat_id
duel_dm_pending = {}  # user_id -> chat_id (menunggu input angka rahasia via DM)

spy_sessions = {}
spy_guess_pending = {}

MAX_RECENT = 300

# =====================
# SLOT CONFIG
# =====================
SLOT_EMOJIS = ["🍎", "🍋", "🍊", "🍇", "⭐", "🎯", "🎰", "💎"]
DIAMOND = "💎"
SLOT_COST = 5_000
SLOT_WIN_NORMAL = 50_000
SLOT_WIN_DIAMOND = 100_000
SLOT_INITIAL = 100_000

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
    name = f"@{user.username}" if user.username else user.first_name
    if uid not in scores[chat_id]:
        scores[chat_id][uid] = {"name": name, "score": 0}
    scores[chat_id][uid]["score"] += points
    scores[chat_id][uid]["name"] = name

def get_nama(user) -> str:
    return f"@{user.username}" if user.username else user.first_name

def format_rupiah(jumlah: int) -> str:
    neg = jumlah < 0
    s = f"{abs(jumlah):,}".replace(",", ".")
    return f"-Rp {s},-" if neg else f"Rp {s},-"

def get_saldo(user_id: int) -> int:
    if user_id not in wallet:
        return SLOT_INITIAL
    return wallet[user_id]["saldo"]

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
