from telegram import Update
from telegram.ext import ContextTypes

from data import (
    wallet, user_badges, SHOP_ITEMS, EXCHANGE_RATES, MAX_BADGES, scores,
    init_wallet, format_rupiah, get_nama, get_raw_name,
    save_wallet, save_badges, save_scores
)

# Dictionary untuk menyimpan konfirmasi penggantian badge tertua
pending_badge_replace = {}  # user_id -> emoji_baru

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    badge_list = user_badges.get(uid, [])
    badge_str = "".join(badge_list) if badge_list else "belum punya"

    text = (
        "🏪 <b>TOKO BADGE KUTIL AJAIB</b> 🏪\n\n"
        "beli badge eksklusif yang akan muncul\n"
        "di username-mu setiap disebut bot!\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        "🛒 <b>DAFTAR BADGE:</b>\n\n"
    )

    for emoji, harga in SHOP_ITEMS.items():
        text += f"  {emoji}  —  <b>{format_rupiah(harga)}</b>\n"

    text += (
        f"\n━━━━━━━━━━━━━━━━━\n"
        f"cara beli:\n"
        f"<code>/beli [emoji]</code>\n\n"
        f"contoh: <code>/beli 💖</code>\n\n"
        f"📌 badge maksimal <b>{MAX_BADGES}</b> buah.\n"
        f"📌 jika sudah penuh, badge baru akan mengganti badge pertama.\n\n"
        f"🏷 badge-mu sekarang: <b>{badge_str}</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>TUKAR SKOR → SALDO</b>\n\n"
    )

    # Tambahkan info penukaran
    sorted_rates = sorted(EXCHANGE_RATES.items())
    for skor, rupiah in sorted_rates:
        text += f"  {skor} poin  →  {format_rupiah(rupiah)}\n"

    text += (
        f"\nketik <code>/tukar [jumlah_skor]</code>\n"
        f"contoh: <code>/tukar 500</code>\n\n"
        f"💡 skor yang ditukar berasal dari papan skor grup ini."
    )

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

    # Ambil badge list saat ini
    current_badges = user_badges.get(uid, [])

    # Cek apakah sudah penuh dan perlu konfirmasi
    if len(current_badges) >= MAX_BADGES:
        # Cek apakah user sudah dalam mode konfirmasi untuk badge yang sama
        pending = pending_badge_replace.get(uid)
        if pending == target_badge:
            # User sudah konfirmasi, lakukan penggantian
            replaced = current_badges.pop(0)  # hapus badge pertama (tertua)
            current_badges.append(target_badge)
            user_badges[uid] = current_badges
            wallet[uid]["saldo"] -= harga
            save_wallet()
            save_badges()

            # Hapus dari pending
            del pending_badge_replace[uid]

            await update.message.reply_text(
                f"✅ <b>BADGE DITAMBAHKAN!</b>\n\n"
                f"{nama}, badge <b>{target_badge}</b> berhasil dibeli.\n"
                f"Karena sudah mencapai batas {MAX_BADGES} badge, badge pertama (<b>{replaced}</b>) dihapus.\n\n"
                f"💳 saldo tersisa: <b>{format_rupiah(wallet[uid]['saldo'])}</b>\n"
                f"🏷 badge-mu sekarang: <b>{''.join(current_badges)}</b>",
                parse_mode="HTML"
            )
        else:
            # Minta konfirmasi
            pending_badge_replace[uid] = target_badge
            await update.message.reply_text(
                f"⚠️ <b>BADGE SUDAH PENUH!</b> ({MAX_BADGES} buah)\n\n"
                f"Jika kamu tetap membeli <b>{target_badge}</b>, badge pertama-mu akan hilang.\n\n"
                f"Ketik lagi <code>/beli {target_badge}</code> untuk melanjutkan pembelian.",
                parse_mode="HTML"
            )
        return
    else:
        # Belum penuh, langsung tambahkan
        current_badges.append(target_badge)
        user_badges[uid] = current_badges
        wallet[uid]["saldo"] -= harga
        save_wallet()
        save_badges()

        # Bersihkan pending jika ada
        pending_badge_replace.pop(uid, None)

        await update.message.reply_text(
            f"🎉 <b>BADGE DIBELI!</b> 🎉\n\n"
            f"selamat {nama}! badge <b>{target_badge}</b> sudah ditambahkan.\n\n"
            f"💳 saldo tersisa: <b>{format_rupiah(wallet[uid]['saldo'])}</b>\n"
            f"🏷 badge-mu sekarang: <b>{''.join(current_badges)}</b>",
            parse_mode="HTML"
        )

async def tukar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menukar skor menjadi saldo."""
    user = update.message.from_user
    chat_id = update.message.chat_id

    if update.message.chat.type == "private":
        await update.message.reply_text("❌ Perintah ini hanya bisa digunakan di grup.")
        return

    if not context.args:
        await update.message.reply_text(
            "💰 <b>TUKAR SKOR → SALDO</b>\n\n"
            "Gunakan: <code>/tukar [jumlah_skor]</code>\n"
            "Pilihan skor: 500, 1000, 2000, 3000\n\n"
            "Contoh: <code>/tukar 1000</code>\n\n"
            "Ketik /shop untuk melihat daftar penukaran.",
            parse_mode="HTML"
        )
        return

    try:
        skor_ditukar = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Jumlah skor harus angka.")
        return

    if skor_ditukar not in EXCHANGE_RATES:
        await update.message.reply_text(
            f"❌ Jumlah skor tidak valid.\n"
            f"Pilihan: {', '.join(str(k) for k in sorted(EXCHANGE_RATES.keys()))}"
        )
        return

    # Cek skor user di grup ini
    if chat_id not in scores:
        await update.message.reply_text("Kamu belum memiliki skor di grup ini.")
        return

    user_score_data = scores[chat_id].get(user.id)
    if not user_score_data:
        await update.message.reply_text("Kamu belum memiliki skor di grup ini.")
        return

    current_score = user_score_data["score"]
    if current_score < skor_ditukar:
        await update.message.reply_text(
            f"❌ Skor kamu tidak cukup.\n"
            f"Skor saat ini: {current_score}\n"
            f"Dibutuhkan: {skor_ditukar}"
        )
        return

    rupiah_didapat = EXCHANGE_RATES[skor_ditukar]

    # Kurangi skor
    user_score_data["score"] -= skor_ditukar
    # Update nama (jika ada perubahan nama dasar)
    user_score_data["name"] = get_raw_name(user)
    save_scores()

    # Tambah saldo
    init_wallet(user)
    wallet[user.id]["saldo"] += rupiah_didapat
    wallet[user.id]["name"] = get_raw_name(user)
    save_wallet()

    await update.message.reply_text(
        f"✅ <b>PENUKARAN BERHASIL!</b>\n\n"
        f"{get_nama(user)} menukar <b>{skor_ditukar} poin</b>\n"
        f"menjadi <b>{format_rupiah(rupiah_didapat)}</b> saldo.\n\n"
        f"💰 saldo sekarang: <b>{format_rupiah(wallet[user.id]['saldo'])}</b>\n"
        f"🏅 sisa skor: <b>{user_score_data['score']}</b>",
        parse_mode="HTML"
    )
