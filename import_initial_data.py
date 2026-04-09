import asyncio
import asyncpg
import os

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL tidak diset. Pastikan environment variable sudah diisi.")

INITIAL_DATA = [
    ("@pemudakhongguan", 11_615_000, []),
    ("@camelliabr", 10_255_000, []),
    ("@lvwonhan", 4_505_000, []),
    ("@badtinnitus", 4_425_000, ["🪽"]),
    ("@cepetanlulus", 4_295_000, []),
    ("@Lailight", 2_500_000, []),
    ("@samvwel", 2_170_000, ["🪽"]),
    ("@linkdivio", 1_930_000, []),
    ("@llaolyd", 95_000, []),
    ("@furabantartika", 50_000, []),
    ("@Vxrtle", 40_000, []),
    ("@Emyuihiy", 25_000, []),
    ("Saya Eriol", 0, []),
    ("@tiramisuacaii", -120_000, []),
]

async def create_tables(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS wallet (
            user_id BIGINT PRIMARY KEY,
            name TEXT NOT NULL,
            saldo INTEGER NOT NULL DEFAULT 100000
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            user_id BIGINT PRIMARY KEY,
            badges TEXT[] NOT NULL DEFAULT '{}'
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            chat_id BIGINT,
            user_id BIGINT,
            name TEXT NOT NULL,
            score INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (chat_id, user_id)
        )
    """)

async def import_data():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await create_tables(conn)

        for username, saldo, badges in INITIAL_DATA:
            user_id = 0
            name = username

            await conn.execute("""
                INSERT INTO wallet (user_id, name, saldo)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO NOTHING
            """, user_id, name, saldo)

            if badges:
                await conn.execute("""
                    INSERT INTO user_badges (user_id, badges)
                    VALUES ($1, $2)
                    ON CONFLICT (user_id) DO NOTHING
                """, user_id, badges)

        print("✅ Data awal berhasil diimpor!")
        print("Catatan: user_id diset 0. Saat user asli muncul, bot akan otomatis memperbarui user_id.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(import_data())
