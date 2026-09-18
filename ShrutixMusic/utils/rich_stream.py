# ShrutixMusic/utils/rich_stream.py
import math
import re

from pyrogram import enums, types

from ShrutixMusic.misc import db
from ShrutixMusic.utils.formatters import time_to_seconds

_TAG_RE = re.compile(r"<(/?)(b|a)(?:\s+href=([^>]+))?>", re.IGNORECASE)


def _parse_inline(segment):
    parts = []
    stack = []
    pos = 0

    for m in _TAG_RE.finditer(segment):
        if m.start() > pos:
            parts.append(segment[pos : m.start()])
        pos = m.end()

        closing, tag, href = m.group(1), m.group(2).lower(), m.group(3)

        if not closing:
            stack.append((tag, href.strip("\"'") if href else None, len(parts)))
        elif stack and stack[-1][0] == tag:
            open_tag, url, start = stack.pop()
            inner = parts[start:]
            del parts[start:]
            inner = inner[0] if len(inner) == 1 else inner if inner else ""
            if open_tag == "b":
                parts.append(types.RichTextBold(text=inner))
            else:
                parts.append(types.RichTextUrl(text=inner, url=url))

    if pos < len(segment):
        parts.append(segment[pos:])

    if not parts:
        return ""
    return parts[0] if len(parts) == 1 else parts


def _html_caption_to_paragraphs(caption_html):
    return [
        types.InputRichBlockParagraph(text=_parse_inline(line))
        for line in caption_html.split("\n")
    ]


def _progress_line(played, dur):
    played_sec = time_to_seconds(played)
    duration_sec = time_to_seconds(dur)
    percentage = (played_sec / duration_sec) * 100 if duration_sec else 0
    umm = math.floor(percentage)
    if 0 < umm <= 10:
        bar = "◉—————————"
    elif 10 < umm < 20:
        bar = "—◉————————"
    elif 20 <= umm < 30:
        bar = "——◉———————"
    elif 30 <= umm < 40:
        bar = "———◉——————"
    elif 40 <= umm < 50:
        bar = "————◉—————"
    elif 50 <= umm < 60:
        bar = "—————◉————"
    elif 60 <= umm < 70:
        bar = "——————◉———"
    elif 70 <= umm < 80:
        bar = "———————◉——"
    elif 80 <= umm < 95:
        bar = "————————◉—"
    else:
        bar = "—————————◉"
    return f"{played}  {bar}  {dur}"


def _queue_len(chat_id):
    tracks = db.get(chat_id)
    return max(len(tracks) - 1, 0) if tracks else 0


def _control_row(chat_id, playing):
    toggle = (
        types.RichMessageButton(
            text="II Pause",
            style=enums.ButtonStyle.DANGER,
            callback_data=f"ADMIN Pause|{chat_id}",
        )
        if playing
        else types.RichMessageButton(
            text="▷ Resume",
            style=enums.ButtonStyle.SUCCESS,
            callback_data=f"ADMIN Resume|{chat_id}",
        )
    )
    return types.InputRichBlockButtons(
        buttons=[
            types.RichMessageButton(
                text="↺ Replay",
                style=enums.ButtonStyle.PRIMARY,
                callback_data=f"ADMIN Replay|{chat_id}",
            ),
            toggle,
            types.RichMessageButton(
                text="» Skip",
                style=enums.ButtonStyle.PRIMARY,
                callback_data=f"ADMIN Skip|{chat_id}",
            ),
            types.RichMessageButton(
                text=f"☰ Queue · {_queue_len(chat_id)}",
                style=enums.ButtonStyle.SUCCESS,
                callback_data=f"nowplaying_queue {chat_id}",
            ),
        ]
    )


def build_now_playing_blocks(photo, caption_html, chat_id, played=None, dur=None, playing=True):
    blocks = [types.InputRichBlockPhoto(photo=types.InputMediaPhoto(photo))]
    blocks += _html_caption_to_paragraphs(caption_html)
    if played and dur:
        blocks.append(types.InputRichBlockParagraph(text=_progress_line(played, dur)))
    blocks.append(_control_row(chat_id, playing))
    return blocks


async def send_now_playing_rich(client, chat_id, target_chat_id, photo, caption_html):
    blocks = build_now_playing_blocks(photo, caption_html, chat_id)
    msg = await client.send_rich_message(
        target_chat_id,
        rich_message=types.InputRichMessage(blocks=blocks),
    )
    if db.get(chat_id):
        db[chat_id][0]["np_photo"] = photo
        db[chat_id][0]["np_caption"] = caption_html
    return msg


async def update_now_playing_progress(mystic, chat_id, played, dur, playing=True):
    info = db.get(chat_id)
    if not info:
        return None
    photo = info[0].get("np_photo")
    caption_html = info[0].get("np_caption")
    if not photo or not caption_html:
        return None
    blocks = build_now_playing_blocks(photo, caption_html, chat_id, played, dur, playing)
    return await mystic.edit_text(rich_message=types.InputRichMessage(blocks=blocks))
