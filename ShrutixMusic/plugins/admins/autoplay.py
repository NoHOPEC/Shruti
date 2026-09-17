# ShrutixMusic/plugins/admins/autoplay.py
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message

from ShrutixMusic import nand
from ShrutixMusic.utils.database import autoplay_off, autoplay_on, is_autoplay
from ShrutixMusic.utils.decorators import AdminRightsCheck
from ShrutixMusic.utils.decorators.admins import ActualAdminCB
from ShrutixMusic.utils.inline.play import autoplay_markup
from config import BANNED_USERS


@nand.on_message(filters.command(["autoplay"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def autoplay_command(client, message: Message, _, chat_id):
    mode = await is_autoplay(chat_id)
    status = "ON ✅" if mode else "OFF ❌"
    text = (
        "🔁 Autoplay\n\n"
        f"Current status: {status}\n\n"
        "When Autoplay is ON, the bot automatically queues and plays a related track "
        "once the current queue runs out, instead of leaving the voice chat."
    )
    markup = InlineKeyboardMarkup([autoplay_markup(chat_id, mode)])
    await message.reply_text(text, reply_markup=markup)


@nand.on_callback_query(filters.regex(r"^autoplay ") & ~BANNED_USERS)
@ActualAdminCB
async def autoplay_toggle(client, CallbackQuery, _):
    chat_id = int(CallbackQuery.data.split(None, 1)[1])
    mode = await is_autoplay(chat_id)

    if mode:
        await autoplay_off(chat_id)
        new_mode = False
        toast = "Autoplay turned OFF"
    else:
        await autoplay_on(chat_id)
        new_mode = True
        toast = "Autoplay turned ON"

    await CallbackQuery.answer(toast, show_alert=False)

    markup = CallbackQuery.message.reply_markup
    if not markup:
        return

    rows = []
    for row in markup.inline_keyboard:
        new_row = []
        for button in row:
            if button.callback_data and button.callback_data.startswith("autoplay "):
                new_row.extend(autoplay_markup(chat_id, new_mode))
            else:
                new_row.append(button)
        rows.append(new_row)

    try:
        await CallbackQuery.message.edit_reply_markup(InlineKeyboardMarkup(rows))
    except Exception:
        pass
