import re

from pyrogram import types

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


def _rich_button_rows(inline_button_rows):
    rows = []
    for row in inline_button_rows:
        buttons = []
        for btn in row:
            if btn.url:
                buttons.append(types.RichMessageButton(text=btn.text, url=btn.url))
            else:
                buttons.append(
                    types.RichMessageButton(text=btn.text, callback_data=btn.callback_data)
                )
        rows.append(types.InputRichBlockButtons(buttons=buttons))
    return rows


async def send_now_playing_rich(client, chat_id, photo, caption_html, inline_button_rows):
    blocks = [types.InputRichBlockPhoto(photo=types.InputMediaPhoto(photo))]
    blocks += _html_caption_to_paragraphs(caption_html)
    blocks += _rich_button_rows(inline_button_rows)

    return await client.send_rich_message(
        chat_id,
        rich_message=types.InputRichMessage(blocks=blocks),
    )
