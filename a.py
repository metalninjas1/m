import asyncio
import sqlite3
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import datetime
import os

# Bot məlumatları
api_id = 13016641
api_hash = 'a8385d296e8b826994bee14b83cf988b'
bot_token = '7286251846:AAFw053eGptYcTEQcXOMZaid1atauM_1urc'
app = Client("future_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Database bağlantıları
conn = sqlite3.connect('bot_data.db')
c = conn.cursor()

# İcazə və mesajlar cədvəli
c.execute('''CREATE TABLE IF NOT EXISTS permissions (user_id INTEGER PRIMARY KEY)''')
c.execute('''CREATE TABLE IF NOT EXISTS saved_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                content TEXT,
                file_path TEXT,
                send_time TEXT
            )''')
conn.commit()

# Mesaj və fayl saxlamaq üçün qovluq
if not os.path.exists("saved_messages"):
    os.mkdir("saved_messages")


# İcazə vermək
@app.on_message(filters.command("grantpermission") & filters.private)
async def grant_permission(client, message: Message):
    user_id = message.from_user.id
    if user_id == 5420622167:  # Admin ID
        await message.reply("🔑 **Parolu daxil edin:**")

        @app.on_message(filters.private)
        async def check_password(client, msg: Message):
            if msg.text == "gizli_parol":  # Parol
                try:
                    target_id = int(msg.reply_to_message.from_user.id)
                    c.execute("INSERT OR IGNORE INTO permissions (user_id) VALUES (?)", (target_id,))
                    conn.commit()
                    await msg.reply("✅ **İcazə uğurla verildi!**")
                except Exception:
                    await msg.reply("⚠️ **Xəta baş verdi.**")
            else:
                await msg.reply("❌ **Parol səhvdir.**")


# Mesaj və ya fayl saxlamaq
@app.on_message(filters.private)
async def handle_message(client, message: Message):
    user_id = message.from_user.id
    c.execute("SELECT user_id FROM permissions WHERE user_id = ?", (user_id,))
    if c.fetchone():
        if message.text or message.media:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Bəli", callback_data="save_yes"),
                 InlineKeyboardButton("Xeyr", callback_data="save_no")]
            ])
            await message.reply("📥 **Bunu saxlamaq istəyirsinizmi?**", reply_markup=keyboard)
    else:
        await message.reply("⚠️ **Bu əmri istifadə etmək səlahiyyətiniz yoxdur.**")


@app.on_callback_query()
async def handle_callback(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    message = callback_query.message

    if data == "save_yes":
        await message.reply("⏳ **Nə qədər vaxta qədər saxlamaq istəyirsiniz? (saatla):**")

        @app.on_message(filters.private)
        async def get_time(client, msg: Message):
            try:
                hours = int(msg.text)
                send_time = (datetime.datetime.now() + datetime.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")

                # Fayl və ya mesajı saxla
                file_path = None
                if message.document or message.photo or message.video:
                    file_name = f"saved_messages/{user_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                    file_path = await message.download(file_name)

                content = message.text or "Fayl"
                c.execute("INSERT INTO saved_messages (user_id, content, file_path, send_time) VALUES (?, ?, ?, ?)",
                          (user_id, content, file_path, send_time))
                conn.commit()

                await msg.reply(f"✅ **Mesaj {hours} saatdan sonra geri göndəriləcək.**")
            except ValueError:
                await msg.reply("⚠️ **Zəhmət olmasa düzgün vaxt daxil edin.**")
    elif data == "save_no":
        await callback_query.message.reply("❌ **Mesaj saxlama prosesi ləğv edildi.**")


# Saxlanmış mesajları yoxla və geri göndər
async def check_scheduled_messages():
    while True:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("SELECT * FROM saved_messages WHERE send_time <= ?", (now,))
        messages = c.fetchall()

        for msg in messages:
            user_id, content, file_path, send_time = msg[1], msg[2], msg[3], msg[4]
            try:
                if file_path:
                    await app.send_document(user_id, file_path)
                else:
                    await app.send_message(user_id, content)

                # Göndərilmiş mesajı sil
                c.execute("DELETE FROM saved_messages WHERE id = ?", (msg[0],))
                conn.commit()
            except Exception as e:
                print(f"Xəta: {e}")
        await asyncio.sleep(60)


if __name__ == "__main__":
    app.start()
    loop = asyncio.get_event_loop()
    loop.create_task(check_scheduled_messages())
    loop.run_forever()
