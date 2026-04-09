import random
from telegram import Update
from telegram.ext import ContextTypes

from data import (
    SLOT_EMOJIS, DIAMOND, SUPER_JACKPOT_EMOJI,
    SLOT_COST, SLOT_WIN_NORMAL, SLOT_WIN_DIAMOND, SLOT_WIN_SUPER, SLOT_INITIAL,
    init_wallet, format_rupiah, get_nama, get_raw_name,
)
from db import db_set_wallet, db_get_all_wallets, db_get_badges, db_get_wallet

async def slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id
    nama = await get_nama(user)

    await init_wallet(user)
    wallet_data = await db_get_wallet(uid)
    saldo = wallet_data["saldo"] if wallet_data else SLOT_INITIAL

    saldo -= SLOT_COST

    reel = [random.choice(SLOT_EMOJIS) for _ in range(3)]
    tampilan = " | ".join(reel)

    semua_sama = reel[0] == reel[1] == reel[2]

    if semua_sama and reel[0] == SUPER_JACKPOT_EMOJI:
        saldo += SLOT_WIN_SUPER
        hasil_teks = (
            f"🪽🪽🪽 <b>SUPER JACKPOT!!</b> 🪽🪽🪽\n\n"
            f"WOOWWW KAMU LUAR BIASA BERUNTUNG!!! 🎉🎉🎉\n\n"
            f"menang <b>{format_rupiah(SLOT_WIN_SUPER)}</b>!"
        )
    elif semua_sama and reel[0] == DIAMOND:
        saldo += SLOT_WIN_DIAMOND
        hasil_teks = (
            f"💎💎💎 <b>JACKPOT DIAMOND!!</b> 💎💎💎\n\n"
            f"kamu beruntung!!! 🤑\n\n"
            f"menang <b>{format_rupiah(SLOT_WIN_DIAMOND)}</b>!"
        )
    elif semua_sama:
        saldo += SLOT_WIN_NORMAL
        hasil_teks = (
            f"🎊 <b>MENANG!</b> kamu beruntung! 🎊\n\n"
            f"menang <b>{format_rupiah(SLOT_WIN_NORMAL)}</b>!"
        )
    else:
        hasil_teks = "😢 tidak ada yang cocok, coba lagi!"

    await db_set_wallet(uid, get_raw_name(user), saldo)

    await update.message.reply_text(
        f"🎰 <b>SLOT MACHINE</b>\n\n"
        f"┌─────────────────┐\n"
        f"│  {tampilan}  │\n"
        f"└─────────────────┘\n\n"
        f"{hasil_teks}\n\n"
        f"💳 saldo: <b>{format_rupiah(saldo)}</b>",
        parse_mode="HTML"
    )

async def kekayaan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = await db_get_all_wallets()
    wallets = [r for r in rows if r["user_id"] != 0]

    if not wallets:
        await update.message.reply_text("belum ada yang main slot!")
        return

    text = "💰 <b>DAFTAR KEKAYAAN PEMAIN</b>\n\n"
    for i, info in enumerate(wallets, 1):
        saldo = info["saldo"]
        uid = info["user_id"]
        raw_name = info["name"]
        badges = await db_get_badges(uid)
        display_name = f"{raw_name} {''.join(badges)}" if badges else raw_name
        emoji = "🤑" if saldo > SLOT_INITIAL else ("😢" if saldo < 0 else "😐")
        text += f"{i}. {display_name} — {format_rupiah(saldo)} {emoji}\n"

    text += f"\n💡 saldo awal: {format_rupiah(SLOT_INITIAL)}\n🎰 bayar per spin: {format_rupiah(SLOT_COST)}"
    await update.message.reply_text(text, parse_mode="HTML")
