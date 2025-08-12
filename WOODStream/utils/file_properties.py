import logging
from datetime import datetime
from pyrogram import Client, errors
from typing import Any, Optional

from pyrogram.enums import ParseMode, ChatType
from pyrogram.types import Message
from pyrogram.file_id import FileId

from WOODStream.bot import WOODStream
from WOODStream.utils.database import Database
from WOODStream.config import Telegram, Server

db = Database(Telegram.DATABASE_URL, Telegram.SESSION_NAME)

# ... (all other functions remain the same) ...

async def send_file(client: Client, db_id, file_id: str, message):
    file_caption = getattr(message, 'caption', None) or get_name(message)
    
    try:
        # Attempt to send the cached media file
        log_msg = await client.send_cached_media(
            chat_id=Telegram.FLOG_CHANNEL, 
            file_id=file_id,
            caption=f'**{file_caption}**'
        )
    except errors.MediaEmpty:
        # This block executes if the file_id is invalid.
        # We need to re-upload the file and update the database.
        logging.warning(f"MediaEmpty error for file with db_id: {db_id}. Re-uploading file.")
        
        # NOTE: You need to have the original file path/URL here. 
        # The provided code snippet doesn't show how the file is stored,
        # but you'd need to fetch the original media data.
        # For this example, let's assume `message` still holds the original media.
        
        # Re-upload the file using the original message object
        if get_media_from_message(message):
            log_msg = await client.copy_message(
                chat_id=Telegram.FLOG_CHANNEL,
                from_chat_id=message.chat.id,
                message_id=message.id,
                caption=f'**{file_caption}**'
            )
            # The new file_id is in the re-uploaded message
            new_file_id = getattr(get_media_from_message(log_msg), 'file_id', '')
            if new_file_id:
                logging.info(f"File re-uploaded. Updating DB with new file_id: {new_file_id}")
                await db.update_file_id(db_id, new_file_id) # You might need to change this call based on your database class
            else:
                logging.error(f"Re-upload failed for db_id: {db_id}. Could not get new file_id.")
                return None
        else:
            logging.error(f"Could not re-upload file for db_id: {db_id} as original media is missing.")
            return None
            
    if message.chat.type == ChatType.PRIVATE:
        await log_msg.reply_text(
            text=f"**RᴇQᴜᴇꜱᴛᴇᴅ ʙʏ :** [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n**Uꜱᴇʀ ɪᴅ :** `{message.from_user.id}`\n**Fɪʟᴇ ɪᴅ :** `{db_id}`",
            disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN, quote=True)
    else:
        await log_msg.reply_text(
            text=f"**RᴇQᴜᴇꜱᴛᴇᴅ ʙʏ :** {message.chat.title} \n**Cʜᴀɴɴᴇʟ ɪᴅ :** `{message.chat.id}`\n**Fɪʟᴇ ɪᴅ :** `{db_id}`",
            disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN, quote=True)

    return log_msg
