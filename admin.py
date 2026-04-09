import os
from telegram import Update
from telegram.ext import ContextTypes
from data import get_nama, format_rupiah, init_wallet, get_raw_name
from db import db_set_wallet, db_get_scores, db_set_score, db_get_wallet_by_name

# Ambil ID admin dari environment variable
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

    target_user = None
    if update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    else:
        username = username_part.lstrip("@")
        found_uid = None
        placeholder = await db_get_wallet_by_name(f"@{username}")
        if placeholder:
            found_uid = 0
            class DummyUser:
                def __init__(self, uid, name):
                    self.id = uid
                    self.username = None
                    self.first_name = name
            target_user = DummyUser(0, placeholder["name"])
        else:
            await update.message.reply_text("user tidak ditemukan. reply pesan user atau pastikan username sudah pernah main slot.")
            return

    uid = target_user.id
    await init_wallet(target_user)
    await db_set_wallet(uid, get_raw_name(target_user), jumlah)

    await update.message.reply_text(
        f"✅ saldo {await get_nama(target_user)} diubah menjadi {format_rupiah(jumlah)}"
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
        placeholder = await db_get_wallet_by_name(f"@{username}")
        if placeholder:
            class DummyUser:
                def __init__(self, uid, name):
                    self.id = uid
                    self.username = None
                    self.first_name = name
            target_user = DummyUser(0, placeholder["name"])
        else:
            await update.message.reply_text("user tidak ditemukan.")
            return

    uid = target_user.id
    await init_wallet(target_user)
    from db import db_get_wallet
    data = await db_get_wallet(uid)
    saldo = data["saldo"] if data else 0
    saldo += tambahan
    await db_set_wallet(uid, get_raw_name(target_user), saldo)

    await update.message.reply_text(
        f"✅ saldo {await get_nama(target_user)} ditambah {format_rupiah(tambahan)}.\n"
        f"saldo sekarang: {format_rupiah(saldo)}"
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
        scores_dict = await db_get_scores(chat_id)
        found_uid = None
        for uid, info in scores_dict.items():
            if info["name"].startswith(f"@{username}"):
                found_uid = uid
                break
        if found_uid:
            class DummyUser:
                def __init__(self, uid, name):
                    self.id = uid
                    self.username = None
                    self.first_name = name
            target_user = DummyUser(found_uid, scores_dict[found_uid]["name"])
        else:
            await update.message.reply_text("user tidak ditemukan di papan skor grup ini.")
            return

    uid = target_user.id
    await db_set_score(chat_id, uid, get_raw_name(target_user), jumlah)

    await update.message.reply_text(
        f"✅ skor {await get_nama(target_user)} di grup ini diubah menjadi {jumlah} poin."
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
        scores_dict = await db_get_scores(chat_id)
        found_uid = None
        for uid, info in scores_dict.items():
            if info["name"].startswith(f"@{username}"):
                found_uid = uid
                break
        if found_uid:
            class DummyUser:
                def __init__(self, uid, name):
                    self.id = uid
                    self.username = None
                    self.first_name = name
            target_user = DummyUser(found_uid, scores_dict[found_uid]["name"])
        else:
            await update.message.reply_text("user tidak ditemukan di papan skor grup ini.")
            return

    uid = target_user.id
    current = (await db_get_scores(chat_id)).get(uid, {}).get("score", 0)
    new_score = current + tambahan
    await db_set_score(chat_id, uid, get_raw_name(target_user), new_score)

    await update.message.reply_text(
        f"✅ skor {await get_nama(target_user)} ditambah {tambahan} poin.\n"
        f"skor sekarang: {new_score}"
    )
