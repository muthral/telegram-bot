from telegram import Update
from telegram.ext import ContextTypes

from data import (
    wallet, user_badges, SHOP_ITEMS,
    init_wallet, format_rupiah, get_nama,
    save_wallet, save_badges
)

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    badge_sekarang = user_badges.get(uid, None)

    text = (
        "🏪 <b>TOKO BADGE KUTIL AJAIB</b> 🏪\n\n"
        "beli badge eksklusif yang akan muncul\n"
        "di username-mu setiap disebut bot!\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        "🛒 <b>DAFTAR BADGE:</b>\n\n"
    )

    for emoji, harga in SHOP_ITEMS.items():
        sudah_punya = badge_sekarang == emoji
        status = " ✅ <i>(milikmu)</i>" if sudah_punya else ""
        text += f"  {emoji}  —  <b>{format_rupiah(harga)}</b>{status}\n"

    text += (
        "\n━━━━━━━━━━━━━━━━━\n"
        "cara beli:\n"
        "<code>/beli [emoji]</code>\n\n"
        "contoh: <code>/beli 💖</code>\n\n"
        "⚠️ <i>beli badge baru akan mengganti badge lama!</i>"
    )

    if badge_sekarang:
        text += f"\n\n🏷 badge-mu sekarang: <b>{badge_sekarang}</b>"

    await update.message.reply_text(text, parse_mode="HTML")

async def beli(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id
    nama = get_nama(user)

    if not context.args:
        await update.message.reply_text(
            "❓ cara beli badge:\n\n"
            "<code>/beli [emoji]</code>\n"
            "contoh: <code>/beli 💖</code>\n\n"
            "lihat daftar badge di /shop",
            parse_mode="HTML"
        )
        return

    target_badge = context.args[0].strip()

    if target_badge not in SHOP_ITEMS:
        tersedia = "  ".join(SHOP_ITEMS.keys())
        await update.message.reply_text(
            f"❌ badge <b>{target_badge}</b> tidak tersedia!\n\n"
            f"badge yang ada:\n{tersedia}\n\n"
            f"ketik /shop untuk lihat harganya",
            parse_mode="HTML"
        )
        return

    harga = SHOP_ITEMS[target_badge]

    init_wallet(user)
    saldo = wallet[uid]["saldo"]

    if saldo < harga:
        kurang = harga - saldo
        await update.message.reply_text(
            f"💸 <b>SALDO TIDAK CUKUP!</b> 💸\n\n"
            f"badge {target_badge} harganya <b>{format_rupiah(harga)}</b>\n"
            f"saldo-mu: <b>{format_rupiah(saldo)}</b>\n\n"
            f"kurang: <b>{format_rupiah(kurang)}</b>\n\n"
            f"😅 main slot dulu biar kaya! /slot",
            parse_mode="HTML"
        )
        return

    badge_lama = user_badges.get(uid)

    wallet[uid]["saldo"] -= harga
    user_badges[uid] = target_badge

    save_wallet()
    save_badges()

    saldo_sisa = wallet[uid]["saldo"]

    ganti_info = f"\n🔄 badge lama ({badge_lama}) sudah diganti!" if badge_lama and badge_lama != target_badge else ""

    await update.message.reply_text(
        f"🎉 <b>BERHASIL BELI BADGE!</b> 🎉\n\n"
        f"selamat {nama}!\n"
        f"badge <b>{target_badge}</b> sudah terpasang!\n\n"
        f"mulai sekarang namamu akan jadi:\n"
        f"<b>{nama}</b>"
        f"{ganti_info}\n\n"
        f"━━━━━━━━━━━━━\n"
        f"💳 saldo tersisa: <b>{format_rupiah(saldo_sisa)}</b>",
        parse_mode="HTML"
    )
