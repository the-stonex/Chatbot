from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from pyrogram.enums import ChatAction, ChatMembersFilter
from pymongo import MongoClient
import os
import random
import time
import asyncio
from datetime import datetime

# ------------------- ENV -------------------
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MONGO_URL = os.environ.get("MONGO_URL")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
UPDATE_CHNL = os.environ.get("UPDATE_CHNL", "")
OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "")
SUPPORT_GRP = os.environ.get("SUPPORT_GRP", "")
BOT_NAME = os.environ.get("BOT_NAME", "CHATBOT")
START_IMG = os.environ.get("START_IMG", "")
STKR = os.environ.get("STKR", "")

# ------------------- CLIENT -------------------
bot = Client("chat-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ------------------- DATABASE -------------------
mongo = MongoClient(MONGO_URL)
vickdb = mongo["VickDb"]["Vick"]
chatai = mongo["Word"]["WordDb"]

# ------------------- BUTTONS -------------------
MAIN_BTN = InlineKeyboardMarkup([
    [InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ", url=f"https://t.me/{OWNER_USERNAME}"),
     InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ", url=f"https://t.me/{SUPPORT_GRP}")],
    [InlineKeyboardButton("ᴀᴅᴅ ᴍᴇ ʙᴀʙʏ", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
    [InlineKeyboardButton("ʜᴇʟᴘ & ᴄᴍᴅs", callback_data="HELP")],
])

HELP_BTN = InlineKeyboardMarkup([
    [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="HELP_BACK")]
])

SOURCE_BTN = InlineKeyboardMarkup([
    [InlineKeyboardButton("sᴏᴜʀᴄᴇ", callback_data='source')],
    [InlineKeyboardButton("ꜱᴜᴘᴘᴏʀᴛ", url=f"https://t.me/{SUPPORT_GRP}"),
     InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="HELP_BACK")]
])

# ------------------- HELPER FUNCTIONS -------------------
async def is_admins(chat_id: int):
    return [m.user.id async for m in bot.get_chat_members(chat_id, filter=ChatMembersFilter.ADMINISTRATORS)]

# ------------------- START -------------------
@bot.on_message(filters.command(["start", f"start@{BOT_USERNAME}"]))
async def start_handler(_, message: Message):
    g = random.choice(["❤️","🎉","✨","🪸","🎉","🎈","🎯"])
    await message.reply_text(g)
    await asyncio.sleep(1)
    await message.reply_sticker(STKR)
    await message.reply_photo(photo=START_IMG, caption=f"**Hey, I am {BOT_NAME}**", reply_markup=MAIN_BTN)

# ------------------- CALLBACKS -------------------
@bot.on_callback_query()
async def cb_handler(_, query: CallbackQuery):
    if query.data == "HELP":
        await query.message.edit_text("Usage of chatbot commands...", reply_markup=HELP_BTN)
    elif query.data == "HELP_BACK":
        await query.message.edit_text(f"**Hey, I am {BOT_NAME}**", reply_markup=MAIN_BTN)
    elif query.data == "source":
        await query.message.edit_text(f"Source code: https://github.com/Noob-mukesh/Chatbot", reply_markup=SOURCE_BTN)

# ------------------- CHATBOT ON/OFF -------------------
@bot.on_message(filters.command(["chatbot on", f"chatbot@{BOT_USERNAME} on"]) & ~filters.private)
async def chatbot_on(_, message: Message):
    if message.from_user.id not in await is_admins(message.chat.id):
        return await message.reply_text("You are not admin!")
    if vickdb.find_one({"chat_id": message.chat.id}):
        vickdb.delete_one({"chat_id": message.chat.id})
        await message.reply_text("Chatbot Enabled!")
    else:
        await message.reply_text("Chatbot Already Enabled!")

@bot.on_message(filters.command(["chatbot off", f"chatbot@{BOT_USERNAME} off"]) & ~filters.private)
async def chatbot_off(_, message: Message):
    if message.from_user.id not in await is_admins(message.chat.id):
        return await message.reply_text("You are not admin!")
    if not vickdb.find_one({"chat_id": message.chat.id}):
        vickdb.insert_one({"chat_id": message.chat.id})
        await message.reply_text("Chatbot Disabled!")
    else:
        await message.reply_text("Chatbot Already Disabled!")

# ------------------- CHATBOT AI -------------------
@bot.on_message((filters.text | filters.sticker) & ~filters.private & ~filters.bot)
async def chatbot_ai(_, message: Message):
    if vickdb.find_one({"chat_id": message.chat.id}):
        return  # chatbot disabled

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    if message.reply_to_message and message.reply_to_message.from_user.id == (await bot.get_me()).id:
        # Bot reply logic
        responses = list(chatai.find({"word": message.text}))
        if responses:
            reply = random.choice(responses)
            if reply["check"] == "sticker":
                await message.reply_sticker(reply["text"])
            else:
                await message.reply_text(reply["text"])
    
    # Learning new replies
    if message.reply_to_message and message.from_user.id != (await bot.get_me()).id:
        if message.text:
            exists = chatai.find_one({"word": message.reply_to_message.text, "text": message.text})
            if not exists:
                chatai.insert_one({"word": message.reply_to_message.text, "text": message.text, "check": "none"})
        if message.sticker:
            exists = chatai.find_one({"word": message.reply_to_message.text, "id": message.sticker.file_unique_id})
            if not exists:
                chatai.insert_one({"word": message.reply_to_message.text, "text": message.sticker.file_id, "check": "sticker", "id": message.sticker.file_unique_id})

# ------------------- RUN -------------------
bot.run()
