import os
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from commands import start, help_cmd, apa, hitung, tagrandom, tag7, skor, track_member
from game_tebak import angka, stoptebak, angkachaos, stopchaos, angkaduel, joinduel, startduel, stopduel
from game_spy import spy, join, startspy, vote, pemain, stopspy, skip
from game_slot import slot, kekayaan
from game_shop import shop, beli
from admin import setsaldo, addsaldo, setscore, addscore

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("TOKEN belum diset")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    app.add_handler(CommandHandler("apa", apa))
    app.add_handler(CommandHandler("hitung", hitung))
    app.add_handler(CommandHandler("tagrandom", tagrandom))
    app.add_handler(CommandHandler("tag7", tag7))
    app.add_handler(CommandHandler("skor", skor))
    app.add_handler(CommandHandler("kekayaan", kekayaan))

    app.add_handler(CommandHandler("angka", angka))
    app.add_handler(CommandHandler("stoptebak", stoptebak))
    app.add_handler(CommandHandler("angkachaos", angkachaos))
    app.add_handler(CommandHandler("stopchaos", stopchaos))
    app.add_handler(CommandHandler("angkaduel", angkaduel))
    app.add_handler(CommandHandler("joinduel", joinduel))
    app.add_handler(CommandHandler("startduel", startduel))
    app.add_handler(CommandHandler("stopduel", stopduel))

    app.add_handler(CommandHandler("slot", slot))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("beli", beli))

    app.add_handler(CommandHandler("spy", spy))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("startspy", startspy))
    app.add_handler(CommandHandler("vote", vote))
    app.add_handler(CommandHandler("pemain", pemain))
    app.add_handler(CommandHandler("stopspy", stopspy))
    app.add_handler(CommandHandler("skip", skip))

    # Admin commands
    app.add_handler(CommandHandler("setsaldo", setsaldo))
    app.add_handler(CommandHandler("addsaldo", addsaldo))
    app.add_handler(CommandHandler("setscore", setscore))
    app.add_handler(CommandHandler("addscore", addscore))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_member))

    print("Bot is running...")
    app.run_polling()
