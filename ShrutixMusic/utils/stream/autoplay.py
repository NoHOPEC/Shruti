# ShrutixMusic/utils/stream/autoplay.py
from pyrogram.types import InlineKeyboardMarkup
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, MediumQualityVideo

from ShrutixMusic import YouTube, nand
from ShrutixMusic.misc import db
from ShrutixMusic.platforms.Youtube import get_autoplay
from ShrutixMusic.utils.database import get_lang, is_autoplay
from ShrutixMusic.utils.formatters import seconds_to_min
from ShrutixMusic.utils.inline.play import stream_markup
from ShrutixMusic.utils.stream.queue import put_queue
from ShrutixMusic.utils.thumbnails import get_thumb
from strings import get_string


async def _first_downloadable(tracks, video: bool):
    for track in tracks:
        next_id = track.get("video_id")
        if not next_id:
            continue

        title = (track.get("title") or "Autoplay Track").title()
        duration_min = seconds_to_min(track.get("duration") or 0)

        file_path, direct = await YouTube.download(
            next_id, None, video=video, videoid=True
        )
        if file_path:
            return next_id, title, duration_min, file_path, direct

    return None


async def try_autoplay(client, chat_id, popped) -> bool:
    if not popped:
        return False

    if not await is_autoplay(chat_id):
        return False

    video_id = popped.get("vidid")
    if not video_id or video_id in ("telegram", "soundcloud"):
        return False

    original_chat_id = popped.get("chat_id")
    video = str(popped.get("streamtype")) == "video"

    try:
        tracks = await get_autoplay(video_id)
    except Exception:
        tracks = []

    if not tracks:
        return False

    picked = await _first_downloadable(tracks, video)
    if not picked:
        return False

    next_id, title, duration_min, file_path, direct = picked

    stream = (
        AudioVideoPiped(
            file_path,
            audio_parameters=HighQualityAudio(),
            video_parameters=MediumQualityVideo(),
        )
        if video
        else AudioPiped(file_path, audio_parameters=HighQualityAudio())
    )

    try:
        await client.change_stream(chat_id, stream)
    except Exception:
        return False

    await put_queue(
        chat_id,
        original_chat_id,
        file_path if direct else f"vid_{next_id}",
        title,
        duration_min,
        "Autoplay",
        next_id,
        nand.id,
        "video" if video else "audio",
    )

    language = await get_lang(original_chat_id)
    _ = get_string(language)
    img = await get_thumb(next_id)
    button = await stream_markup(_, chat_id)

    run = await nand.send_photo(
        chat_id=original_chat_id,
        photo=img,
        caption=_["stream_1"].format(
            f"https://t.me/{nand.username}?start=info_{next_id}",
            title[:23],
            duration_min,
            "Autoplay",
        ),
        reply_markup=InlineKeyboardMarkup(button),
    )
    db[chat_id][0]["mystic"] = run
    db[chat_id][0]["markup"] = "stream"
    return True
