import asyncio
import datetime
import logging
from pytz import timezone
from dateutil.relativedelta import relativedelta
from antigcast import Bot
from pyrogram import filters
from pyrogram.types import Message
from antigcast.config import OWNER_ID
from antigcast.helpers.tools import get_arg
from antigcast.helpers.database import (
    list_sellers,
    get_actived_chats,
    add_actived_chat,
    set_expired_date,
    save_seller_info,
    rem_actived_chat,
    rem_expired_date,
    add_seller,
    rem_seller,
    list_sellers,
    get_expired_date,
    get_seller_info
)

# Setup logging
logging.basicConfig(level=logging.INFO)


async def is_seller(user_id):
    """Periksa apakah pengguna adalah penjual."""
    sellers = await list_sellers()
    return any(seller['_id'] == user_id for seller in sellers)


@Bot.on_message(filters.command("addgc"))
async def addgcmessag(app: Bot, message: Message):
    """Menambahkan izin untuk grup tertentu."""
    if not await is_seller(message.from_user.id):
        return await message.reply("Anda tidak diizinkan untuk menggunakan perintah ini.")
    
    chat_id = message.chat.id
    chat_name = message.chat.title or "Tidak diketahui"
    seller_id = message.from_user.id
    username = message.from_user.username or "Tidak diketahui"
    name = message.from_user.first_name + (
        " " + message.from_user.last_name if message.from_user.last_name else ""
    )
    
    hari = get_arg(message)
    try:
        hari = int(hari) if hari else 30
    except ValueError:
        return await message.reply("Jumlah hari harus berupa angka.")

    xxnx = await message.reply("Menambahkan izin dalam grup ini...")
    now = datetime.datetime.now(timezone("Asia/Jakarta"))
    expired = now + relativedelta(days=hari)
    expired_date = expired.strftime("%d-%m-%Y")

    chats = await get_actived_chats()
    if chat_id in chats:
        msg = await message.reply("Maaf, grup ini sudah diizinkan untuk menggunakan Bot.")
        await asyncio.sleep(10)
        await msg.delete()
        return

    try:
        added = await add_actived_chat(chat_id)
        if added:
            await set_expired_date(chat_id, expired)
            await save_seller_info(chat_id, seller_id, username, name)
    except Exception as e:
        logging.error(f"Error adding group {chat_id}: {e}")
        return await xxnx.edit("Terjadi kesalahan saat menambahkan grup.")

    await xxnx.edit(f"BOT AKTIF\nGrup : {chat_name}\nExp : {expired_date} | {hari} Hari..\nDitambahkan oleh: {name} (@{username})")
    await asyncio.sleep(10)
    await xxnx.delete()
    await message.delete()


@Bot.on_message(filters.command("add"))
async def addgroupmessag(app: Bot, message: Message):
    """Menambahkan izin untuk grup menggunakan ID grup dan durasi."""
    if not await is_seller(message.from_user.id):
        return await message.reply("Anda tidak diizinkan untuk menggunakan perintah ini.")
    
    seller_id = message.from_user.id
    username = message.from_user.username or "Tidak diketahui"
    name = message.from_user.first_name + (
        " " + message.from_user.last_name if message.from_user.last_name else ""
    )
    xxnx = await message.reply("Menambahkan izin dalam grup ini...")
    
    if len(message.command) < 3:
        return await xxnx.edit("Gunakan Format: /add group_id hari")
    
    try:
        command, group, hari = message.command[:3]
        chat_id = int(group)
        days = int(hari)
    except ValueError:
        return await xxnx.edit("Group ID dan hari harus berupa angka.")
    
    now = datetime.datetime.now(timezone("Asia/Jakarta"))
    expired = now + relativedelta(days=days)
    expired_date = expired.strftime("%d-%m-%Y")
    
    chats = await get_actived_chats()
    if chat_id in chats:
        msg = await message.reply("Maaf, grup ini sudah diizinkan untuk menggunakan Bot.")
        await asyncio.sleep(10)
        await msg.delete()
        return
    
    try:
        added = await add_actived_chat(chat_id)
        if added:
            await set_expired_date(chat_id, expired)
            await save_seller_info(chat_id, seller_id, username, name)
    except Exception as e:
        logging.error(f"Error adding group {chat_id}: {e}")

    await xxnx.edit(f"BOT AKTIF\nGroup ID: {group}\nExp : {expired_date} | {hari} Hari..\nDitambahkan oleh: {name} (@{username})")
    await asyncio.sleep(10)
    await xxnx.delete()
    await message.delete()


@Bot.on_message(filters.command("rmgc") & filters.user(OWNER_ID))
async def remgcmessag(app: Bot, message: Message):
    """Menghapus izin grup."""
    arg = get_arg(message)
    if not arg:
        return await message.reply("Anda harus menyediakan ID grup untuk menghapus izin.")

    try:
        chat_id = int(arg)
    except ValueError:
        return await message.reply("ID grup harus berupa angka yang valid.")

    xxnx = await message.reply("Menghapus izin dalam grup ini...")
    try:
        await rem_actived_chat(chat_id)
        await rem_expired_date(chat_id)
    except Exception as e:
        logging.error(f"Error removing group {chat_id}: {e}")

    await xxnx.edit(f"Removed {chat_id} | Grup ini tidak diizinkan untuk menggunakan Bot.")
    await asyncio.sleep(10)
    await xxnx.delete()
    await message.delete()


@Bot.on_message(filters.command("groups"))
async def get_groupsmessag(app: Bot, message: Message):
    """Menampilkan daftar grup yang terdaftar."""
    if not await is_seller(message.from_user.id):
        return await message.reply("Anda tidak diizinkan untuk menggunakan perintah ini.")
    
    group = []
    chats = await get_actived_chats()
    for chat in chats:
        group.append(chat)
    if not group:
        return await message.reply("Belum ada grup yang terdaftar.")
    
    resp = await message.reply("Memuat database...")
    msg = f"Daftar Grup Aktif\n\n"
    num = 0
    for gc in group:
        expired = await get_expired_date(int(gc))
        seller_info = await get_seller_info(int(gc))
        expired_date = expired.strftime("%d-%m-%Y") if expired else "None"
        seller_name = seller_info.get("name", "Unknown") if seller_info else "Unknown"
        seller_username = seller_info.get("username", "Unknown") if seller_info else "Unknown"
        try:
            get = await app.get_chat(int(gc))
            gname = get.title
            glink = get.invite_link
            gid = get.id
            num += 1
            msg += (
                f"{num}. {gname}\n"
                f"├ Group ID : {gid}\n"
                f"├ Link : [Tap Here]({glink})\n"
                f"├ Expired : {expired_date}\n"
                f"└ Ditambahkan oleh: {seller_name} (@{seller_username})\n\n"
            )
        except Exception:
            msg += (
                f"{num}. {gc}\n"
                f"├ Expired : {expired_date}\n"
                f"└ Ditambahkan oleh: {seller_name} (@{seller_username})\n\n"
            )

    await resp.edit(msg, disable_web_page_preview=True)


@Bot.on_message(filters.command("addseller") & filters.user(OWNER_ID))
async def addsellermessag(app: Bot, message: Message):
    """Menambahkan penjual baru."""
    xxnx = await message.reply("Menambahkan penjual baru...")

    if message.reply_to_message:
        seller_id = message.reply_to_message.from_user.id
    elif len(message.command) == 2:
        try:
            seller_id = int(message.command[1])
        except ValueError:
            return await xxnx.edit("Seller ID harus berupa angka.")
    else:
        return await xxnx.edit("Gunakan Format : /addseller seller_id atau reply ke pesan user.")

    try:
        added_at = datetime.datetime.now(timezone('Asia/Jakarta'))
        added = await add_seller(seller_id, added_at)
        if added:
            await xxnx.edit(f"Penjual Ditambahkan\nSeller ID: {seller_id}\nAdded At: {added_at.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            await xxnx.edit("Gagal menambahkan penjual.")
    except Exception as e:
        logging.error(f"Error adding seller {seller_id}: {e}")
        await xxnx.edit("Terjadi kesalahan saat menambahkan penjual.")
        

@Bot.on_message(filters.command("delseller") & filters.user(OWNER_ID))
async def delsellermessag(app: Bot, message: Message):
    """Menghapus penjual dari daftar."""
    xxnx = await message.reply("Menghapus penjual...")

    if message.reply_to_message:
        seller_id = message.reply_to_message.from_user.id
    elif len(message.command) == 2:
        try:
            seller_id = int(message.command[1])
        except ValueError:
            return await xxnx.edit("Seller ID harus berupa angka.")
    else:
        return await xxnx.edit("Gunakan Format : /delseller seller_id atau reply ke pesan user.")

    try:
        removed = await rem_seller(seller_id)
        if removed:
            await xxnx.edit(f"Penjual Dihapus\nSeller ID: {seller_id}")
        else:
            await xxnx.edit("Penjual tidak ditemukan.")
    except Exception as e:
        logging.error(f"Error removing seller {seller_id}: {e}")
        await xxnx.edit("Terjadi kesalahan saat menghapus penjual.")


@Bot.on_message(filters.command("sellers") & filters.user(OWNER_ID))
async def listsellermessag(app: Bot, message: Message):
    """Menampilkan daftar penjual yang terdaftar."""
    xxnx = await message.reply("Memuat database...")

    sellers = await list_sellers()
    if not sellers:
        return await xxnx.edit("Tidak ada penjual yang terdaftar.")

    msg = "**Daftar Seller**\n\n"
    for num, seller in enumerate(sellers, start=1):
        added_at = seller.get("added_at", "Tidak diketahui")
        added_at_str = added_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(added_at, datetime.datetime) else "Tidak diketahui"
        msg += f"{num}. Seller ID: `{seller['_id']}`\n   Added at: {added_at_str}\n\n"

    await xxnx.edit(msg)
