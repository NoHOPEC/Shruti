from pyrogram import raw, utils as pyroutils


def _peer_to_chat_id(peer):
    if isinstance(peer, raw.types.PeerChannel):
        return pyroutils.get_channel_id(peer.channel_id)
    if isinstance(peer, raw.types.PeerChat):
        return -peer.chat_id
    if isinstance(peer, raw.types.PeerUser):
        return peer.user_id
    return None


def apply():
    cls = raw.types.UpdateGroupCall
    if hasattr(cls, "chat_id"):
        return

    def chat_id(self):
        return _peer_to_chat_id(getattr(self, "peer", None))

    cls.chat_id = property(chat_id)
