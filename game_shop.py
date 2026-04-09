from telegram import Update
from telegram.ext import ContextTypes
from data import (
    SHOP_ITEMS, EXCHANGE_RATES, MAX_BADGES,
    init_wallet, format_rupiah, get_nama, get_raw_name,
    db_get_wallet, db_set_wallet, db_get_badges, db_set_badges,
    db_get_scores, db_set_score
)

pending_badge_replace = {}

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    badge_list = await db_get_badges(uid)
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
    nama = await get_nama(user)

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
    await init_wallet(user)
    wallet_data = await db_get_wallet(uid)
    saldo = wallet_data["saldo"] if wallet_data else 0

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

    current_badges = await db_get_badges(uid)

    if len(current_badges) >= MAX_BADGES:
        pending = pending_badge_replace.get(uid)
        if pending == target_badge:
            replaced = current_badges.pop(0)
            current_badges.append(target_badge)
            await db_set_badges(uid, current_badges)
            saldo -= harga
            await db_set_wallet(uid, get_raw_name(user), saldo)
            del pending_badge_replace[uid]

            await update.message.reply_text(
                f"✅ <b>BADGE DITAMBAHKAN!</b>\n\n"
                f"{nama}, badge <b>{target_badge}</b> berhasil dibeli.\n"
                f"Karena sudah mencapai batas {MAX_BADGES} badge, badge pertama (<b>{replaced}</b>) dihapus.\n\n"
                f"💳 saldo tersisa: <b>{format_rupiah(saldo)}</b>\n"
                f"🏷 badge-mu sekarang: <b>{''.join(current_badges)}</b>",
                parse_mode="HTML"
            )
        else:
            pending_badge_replace[uid] = target_badge
            await update.message.reply_text(
                f"⚠️ <b>BADGE SUDAH PENUH!</b> ({MAX_BADGES} buah)\n\n"
                f"Jika kamu tetap membeli <b>{target_badge}</b>, badge pertama-mu akan hilang.\n\n"
                f"Ketik lagi <code>/beli {target_badge}</code> untuk melanjutkan pembelian.",
                parse_mode="HTML"
            )
        return
    else:
        current_badges.append(target_badge)
        await db_set_badges(uid, current_badges)
        saldo -= harga
        await db_set_wallet(uid, get_raw_name(user), saldo)
        pending_badge_replace.pop(uid, None)

        await update.message.reply_text(
            f"🎉 <b>BADGE DIBELI!</b> 🎉\n\n"
            f"selamat {nama}! badge <b>{target_badge}</b> sudah ditambahkan.\n\n"
            f"💳 saldo tersisa: <b>{format_rupiah(saldo)}</b>\n"
            f"🏷 badge-mu sekarang: <b>{''.join(current_badges)}</b>",
            parse_mode="HTML"
        )

async def tukar(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    scores_dict = await db_get_scores(chat_id)
    if user.id not in scores_dict:
        await update.message.reply_text("Kamu belum memiliki skor di grup ini.")
        return

    current_score = scores_dict[user.id]["score"]
    if current_score < skor_ditukar:
        await update.message.reply_text(
            f"❌ Skor kamu tidak cukup.\n"
            f"Skor saat ini: {current_score}\n"
            f"Dibutuhkan: {skor_ditukar}"
        )
        return

    rupiah_didapat = EXCHANGE_RATES[skor_ditukar]

    # Kurangi skor
    new_score = current_score - skor_ditukar
    await db_set_score(chat_id, user.id, get_raw_name(user), new_score)

    # Tambah saldo
    await init_wallet(user)
    wallet_data = await db_get_wallet(user.id)
    saldo = wallet_data["saldo"] if wallet_data else SLOT_INITIAL
    saldo += rupiah_didapat
    await db_set_wallet(user.id, get_raw_name(user), saldo)

    await update.message.reply_text(
        f"✅ <b>PENUKARAN BERHASIL!</b>\n\n"
        f"{await get_nama(user)} menukar <b>{skor_ditukar} poin</b>\n"
        f"menjadi <b>{format_rupiah(rupiah_didapat)}</b> saldo.\n\n"
        f"💰 saldo sekarang: <b>{format_rupiah(saldo)}</b>\n"
        f"🏅 sisa skor: <b>{new_score}</b>",
        parse_mode="HTML"
    )
