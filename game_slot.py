import random
from telegram import Update
from telegram.ext import ContextTypes

from data import (
    wallet, SLOT_EMOJIS, DIAMOND,
    SLOT_COST, SLOT_WIN_NORMAL, SLOT_WIN_DIAMOND, SLOT_INITIAL,
    init_wallet, get_saldo, format_rupiah, get_nama
)

async def slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id
    nama = get_nama(user)

    init_wallet(user)

    wallet[uid]["saldo"] -= SLOT_COST

    reel = [random.choice(SLOT_EMOJIS) for _ in range(3)]
    tampilan = " | ".join(reel)

    semua_sama = reel[0] == reel[1] == reel[2]

    if semua_sama and reel[0] == DIAMOND:
        wallet[uid]["saldo"] += SLOT_WIN_DIAMOND
        hasil_teks = (
            f"💎💎💎 <b>JACKPOT DIAMOND!!</b> 💎💎💎\n\n"
            f"kamu beruntung!!! 🤑\n\n"
            f"menang <b>{format_rupiah(SLOT_WIN_DIAMOND)}</b>!"
        )
    elif semua_sama:
        wallet[uid]["saldo"] += SLOT_WIN_NORMAL
        hasil_teks = (
            f"🎊 <b>MENANG!</b> kamu beruntung! 🎊\n\n"
            f"menang <b>{format_rupiah(SLOT_WIN_NORMAL)}</b>!"
        )
    else:
        hasil_teks = "😢 tidak ada yang cocok, coba lagi!"

    saldo_akhir = wallet[uid]["saldo"]

    await update.message.reply_text(
        f"🎰 <b>SLOT MACHINE</b>\n\n"
        f"┌─────────────────┐\n"
        f"│  {tampilan}  │\n"
        f"└─────────────────┘\n\n"
        f"{hasil_teks}\n\n"
        f"💳 saldo: <b>{format_rupiah(saldo_akhir)}</b>",
        parse_mode="HTML"
    )

async def kekayaan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not wallet:
        await update.message.reply_text("belum ada yang main slot!")
        return

    sorted_wallet = sorted(wallet.items(), key=lambda x: x[1]["saldo"], reverse=True)

    text = "💰 <b>DAFTAR KEKAYAAN PEMAIN</b>\n\n"
    for i, (uid, info) in enumerate(sorted_wallet, 1):
        saldo = info["saldo"]
        nama = info["name"]
        emoji = "🤑" if saldo > SLOT_INITIAL else ("😢" if saldo < 0 else "😐")
        text += f"{i}. {nama} — {format_rupiah(saldo)} {emoji}\n"

    text += f"\n💡 saldo awal: {format_rupiah(SLOT_INITIAL)}\n🎰 bayar per spin: {format_rupiah(SLOT_COST)}"

    await update.message.reply_text(text, parse_mode="HTML")
