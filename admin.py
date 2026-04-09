import os
from telegram import Update
from telegram.ext import ContextTypes
from data import wallet, scores, save_wallet, save_scores, get_nama, format_rupiah, init_wallet

# Ambil ID admin dari environment variable, pisahkan dengan koma
ADMIN_IDS_STR = os.environ.get("BOT_ADMIN_IDS", "")
ADMIN_IDS = set()
for part in ADMIN_IDS_STR.split(","):
    part = part.strip()
    if part.isdigit():
        ADMIN_IDS.add(int(part))

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def setsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ kamu bukan admin bot.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("gunakan: /setsaldo @username jumlah")
        return

    username_part = context.args[0]
    jumlah_str = context.args[1]

    if not jumlah_str.lstrip("-").isdigit():
        await update.message.reply_text("jumlah harus angka.")
        return

    jumlah = int(jumlah_str)

    # Cari user berdasarkan username
    target_user = None
    if username_part.startswith("@"):
        username = username_part[1:]
    else:
        username = username_part

    # Karena kita tidak bisa mendapatkan user objek langsung dari username tanpa update,
    # kita coba dari data wallet yang ada, atau minta mention.
    # Alternatif: bisa menggunakan fitur mention di pesan.
    # Untuk kemudahan, kita minta user di-mention atau reply.
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    else:
        # Coba cari di wallet berdasarkan username yang tersimpan
        found_uid = None
        for uid, data in wallet.items():
            if data.get("name", "").startswith(f"@{username}"):
                found_uid = uid
                break
        if found_uid:
            # Buat dummy user object (tidak ideal, tapi cukup untuk ID)
            class DummyUser:
                def __init__(self, uid, name):
                    self.id = uid
                    self.username = None
                    self.first_name = name
            target_user = DummyUser(found_uid, wallet[found_uid]["name"])
        else:
            await update.message.reply_text("user tidak ditemukan. reply pesan user atau pastikan username sudah pernah main slot.")
            return

    uid = target_user.id
    init_wallet(target_user)  # pastikan wallet ada
    wallet[uid]["saldo"] = jumlah
    wallet[uid]["name"] = get_nama(target_user)  # update nama
    save_wallet()

    await update.message.reply_text(
        f"✅ saldo {get_nama(target_user)} diubah menjadi {format_rupiah(jumlah)}"
    )

async def addsaldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ kamu bukan admin bot.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("gunakan: /addsaldo @username jumlah")
        return

    username_part = context.args[0]
    jumlah_str = context.args[1]

    if not jumlah_str.lstrip("-").isdigit():
        await update.message.reply_text("jumlah harus angka.")
        return

    tambahan = int(jumlah_str)

    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    else:
        username = username_part.lstrip("@")
        found_uid = None
        for uid, data in wallet.items():
            if data.get("name", "").startswith(f"@{username}"):
                found_uid = uid
                break
        if found_uid:
            class DummyUser:
                def __init__(self, uid, name):
                    self.id = uid
                    self.username = None
                    self.first_name = name
            target_user = DummyUser(found_uid, wallet[found_uid]["name"])
        else:
            await update.message.reply_text("user tidak ditemukan.")
            return

    uid = target_user.id
    init_wallet(target_user)
    wallet[uid]["saldo"] += tambahan
    wallet[uid]["name"] = get_nama(target_user)
    save_wallet()

    await update.message.reply_text(
        f"✅ saldo {get_nama(target_user)} ditambah {format_rupiah(tambahan)}.\n"
        f"saldo sekarang: {format_rupiah(wallet[uid]['saldo'])}"
    )

async def setscore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ kamu bukan admin bot.")
        return

    if update.message.chat.type == "private":
        await update.message.reply_text("command ini hanya untuk grup.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("gunakan: /setscore @username jumlah")
        return

    username_part = context.args[0]
    jumlah_str = context.args[1]

    if not jumlah_str.lstrip("-").isdigit():
        await update.message.reply_text("jumlah harus angka.")
        return

    jumlah = int(jumlah_str)

    chat_id = update.message.chat_id

    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    else:
        username = username_part.lstrip("@")
        # Cari di scores[chat_id]
        found_uid = None
        if chat_id in scores:
            for uid, info in scores[chat_id].items():
                if info.get("name", "").startswith(f"@{username}"):
                    found_uid = uid
                    break
        if found_uid:
            class DummyUser:
                def __init__(self, uid, name):
                    self.id = uid
                    self.username = None
                    self.first_name = name
            target_user = DummyUser(found_uid, scores[chat_id][found_uid]["name"])
        else:
            await update.message.reply_text("user tidak ditemukan di papan skor grup ini.")
            return

    uid = target_user.id
    if chat_id not in scores:
        scores[chat_id] = {}
    if uid not in scores[chat_id]:
        scores[chat_id][uid] = {"name": get_nama(target_user), "score": 0}
    scores[chat_id][uid]["score"] = jumlah
    scores[chat_id][uid]["name"] = get_nama(target_user)
    save_scores()

    await update.message.reply_text(
        f"✅ skor {get_nama(target_user)} di grup ini diubah menjadi {jumlah} poin."
    )

async def addscore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ kamu bukan admin bot.")
        return

    if update.message.chat.type == "private":
        await update.message.reply_text("command ini hanya untuk grup.")
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("gunakan: /addscore @username jumlah")
        return

    username_part = context.args[0]
    jumlah_str = context.args[1]

    if not jumlah_str.lstrip("-").isdigit():
        await update.message.reply_text("jumlah harus angka.")
        return

    tambahan = int(jumlah_str)

    chat_id = update.message.chat_id

    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    else:
        username = username_part.lstrip("@")
        found_uid = None
        if chat_id in scores:
            for uid, info in scores[chat_id].items():
                if info.get("name", "").startswith(f"@{username}"):
                    found_uid = uid
                    break
        if found_uid:
            class DummyUser:
                def __init__(self, uid, name):
                    self.id = uid
                    self.username = None
                    self.first_name = name
            target_user = DummyUser(found_uid, scores[chat_id][found_uid]["name"])
        else:
            await update.message.reply_text("user tidak ditemukan di papan skor grup ini.")
            return

    uid = target_user.id
    if chat_id not in scores:
        scores[chat_id] = {}
    if uid not in scores[chat_id]:
        scores[chat_id][uid] = {"name": get_nama(target_user), "score": 0}
    scores[chat_id][uid]["score"] += tambahan
    scores[chat_id][uid]["name"] = get_nama(target_user)
    save_scores()

    await update.message.reply_text(
        f"✅ skor {get_nama(target_user)} ditambah {tambahan} poin.\n"
        f"skor sekarang: {scores[chat_id][uid]['score']}"
    )
