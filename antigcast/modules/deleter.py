import asyncio
import logging
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, MessageDeleteForbidden, UserNotParticipant
from antigcast import Bot
from antigcast.config import *
from antigcast.helpers.tools import get_arg
from antigcast.helpers.admins import Admin
from antigcast.helpers.database import (
    add_bl_word,
    remove_bl_word,
    get_actived_chats
)

# Setup logging
logging.basicConfig(level=logging.INFO)

@Bot.on_message(filters.command("addbl") & ~filters.private & Admin)
async def add_blacklist_message(app: Bot, message: Message):
    """Menambahkan kata ke dalam blacklist."""
    trigger = get_arg(message)
    if message.reply_to_message:
        trigger = message.reply_to_message.text or message.reply_to_message.caption

    if not trigger:
        return await message.reply("Anda harus menentukan kata atau frasa untuk ditambahkan ke blacklist.")

    xxnx = await message.reply(f"`Menambahkan` {trigger} `ke dalam blacklist...`")
    try:
        await add_bl_word(trigger.lower())
        await xxnx.edit(f"`{trigger}` berhasil ditambahkan ke dalam blacklist.")
    except Exception as e:
        logging.error(f"Error saat menambahkan {trigger} ke blacklist: {e}")
        await xxnx.edit(f"Error: `{e}`")
    finally:
        await asyncio.sleep(5)
        await xxnx.delete()
        await message.delete()

@Bot.on_message(filters.command("delbl") & ~filters.private & Admin)
async def delete_blacklist_message(app: Bot, message: Message):
    """Menghapus kata dari blacklist."""
    trigger = get_arg(message)
    if message.reply_to_message:
        trigger = message.reply_to_message.text or message.reply_to_message.caption

    if not trigger:
        return await message.reply("Anda harus menentukan kata atau frasa untuk dihapus dari blacklist.")

    xxnx = await message.reply(f"`Menghapus` {trigger} `dari blacklist...`")
    try:
        await remove_bl_word(trigger.lower())
        await xxnx.edit(f"`{trigger}` berhasil dihapus dari blacklist.")
    except Exception as e:
        logging.error(f"Error saat menghapus {trigger} dari blacklist: {e}")
        await xxnx.edit(f"Error: `{e}`")
    finally:
        await asyncio.sleep(5)
        await xxnx.delete()
        await message.delete()

@Bot.on_message(filters.text & filters.group, group=56)
async def delete_unregistered_message(app: Bot, message: Message):
    """Menghapus pesan di grup yang tidak terdaftar dan meninggalkan grup."""
    text = (
        "Maaf, grup ini tidak terdaftar dalam daftar yang diizinkan. "
        "Silakan hubungi owner untuk mendaftarkan grup Anda.\n\n**Bot akan meninggalkan grup!**"
    )
    chat_id = message.chat.id
    chats = await get_actived_chats()
    
    # Cek apakah pesan adalah pesan gcast (broadcast global)
    if await isGcast(filters, app, message):
        try:
            await message.delete()
        except FloodWait as e:
            logging.warning(f"FloodWait terjadi, menunggu {e.x} detik.")
            await asyncio.sleep(e.x)
            await message.delete()
        except MessageDeleteForbidden:
            logging.warning(f"Tidak dapat menghapus pesan di grup {chat_id}")
        return
    
    # Jika grup tidak terdaftar, berikan peringatan dan tinggalkan grup
    if chat_id not in chats:
        warning_message = await message.reply(text)
        await asyncio.sleep(5)
        await warning_message.delete()
        try:
            await app.leave_chat(chat_id)
            logging.info(f"Bot meninggalkan grup yang tidak terdaftar: {chat_id}")
        except UserNotParticipant:
            logging.warning(f"Bot sudah bukan anggota dari grup {chat_id}.")
        except Exception as e:
            logging.error(f"Kesalahan saat mencoba meninggalkan grup {chat_id}: {e}")
