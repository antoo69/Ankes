import os
import sys
import asyncio
import subprocess
import logging

from antigcast import Bot
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

from antigcast.config import BROADCAST_AS_COPY, CREATOR
from antigcast.helpers.tools import get_arg, send_large_output
from antigcast.helpers.database import get_actived_chats

# Setup logging
logging.basicConfig(level=logging.INFO)

async def send_msg(chat_id, message: Message):
    """Mengirim pesan ke grup atau pengguna tertentu."""
    try:
        if BROADCAST_AS_COPY:
            await message.copy(chat_id=chat_id)
        else:
            await message.forward(chat_id=chat_id)
        return 200, None
    except FloodWait as e:
        logging.warning(f"FloodWait terjadi, menunggu {e.value} detik untuk chat_id: {chat_id}")
        await asyncio.sleep(e.value)
        return await send_msg(chat_id, message)
    except Exception as e:
        logging.error(f"Gagal mengirim pesan ke {chat_id}: {e}")
        return None, e

@Bot.on_message(filters.command("update") & ~filters.private & filters.user(CREATOR))
async def handle_update(app: Bot, message: Message):
    """Menangani perintah update bot menggunakan git pull."""
    try:
        out = subprocess.check_output(["git", "pull"], stderr=subprocess.STDOUT).decode("UTF-8")
        if "Already up to date." in out:
            await message.reply(out, quote=True)
        elif len(out) > 4096:
            await send_large_output(message, out)
        else:
            await message.reply(f"```{out}```", quote=True)
        
        # Restart bot setelah update
        os.execl(sys.executable, sys.executable, "-m", "antigcast")
    except subprocess.CalledProcessError as e:
        logging.error(f"Git pull failed with error code {e.returncode}: {e.output.decode('UTF-8')}")
        await message.reply(f"Git pull failed with error code {e.returncode}:\n{e.output.decode('UTF-8')}", quote=True)
    except Exception as e:
        logging.error(f"Kesalahan saat mencoba update: {e}")
        await message.reply(f"An error occurred while trying to update:\n{str(e)}", quote=True)

@Bot.on_message(filters.command("restart") & filters.user(CREATOR))
async def handle_restart(app: Bot, message: Message):
    """Menangani perintah restart bot."""
    try:
        await message.reply("✅ System berhasil direstart", quote=True)
        os.execl(sys.executable, sys.executable, "-m", "antigcast")
    except Exception as e:
        logging.error(f"Kesalahan saat mencoba restart: {e}")
        await message.reply(f"An error occurred while trying to restart:\n{str(e)}", quote=True)

@Bot.on_message(filters.command("gcast") & filters.user(CREATOR))
async def gcast_handler(app: Bot, message: Message):
    """Menangani perintah gcast untuk mengirim pesan ke semua grup terdaftar."""
    groups = await get_actived_chats()
    msg = message.reply_to_message if message.reply_to_message else get_arg(message)

    if not msg:
        await message.reply("**Reply atau berikan saya sebuah pesan!**")
        return
    
    out = await message.reply("**Memulai Broadcast...**")
    
    if not groups:
        await out.edit("**Maaf, Broadcast Gagal Karena Belum Ada Grup Yang Terdaftar**")
        return
    
    done, failed = 0, 0
    for group in groups:
        status, error = await send_msg(group, message=msg)
        if status == 200:
            done += 1
        else:
            failed += 1
            logging.warning(f"Gagal mengirim pesan ke grup {group}: {error}")
    
    await out.edit(f"**Berhasil Mengirim Pesan Ke {done} Grup.**\n**Gagal Mengirim Pesan Ke {failed} Grup.**")
