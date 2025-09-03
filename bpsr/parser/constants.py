from __future__ import annotations

from enum import IntEnum


class MessageType(IntEnum):
    NONE = 0
    CALL = 1
    NOTIFY = 2
    RETURN = 3
    ECHO = 4
    FRAME_UP = 5
    FRAME_DOWN = 6
    ACK_FRAME_UP = 7
    ACK_FRAME_DOWN = 8
    REWIND_FRAME = 9
    CALL_INNER = 10
    NOTIFY_INNER = 11
    BROADCAST = 12
    BROADCAST_BY_SESSION = 13
    TERMINATE = 14


class ServiceID:
    WORLD_NTF = 0x0000000063335342
    CHIT_CHAT_NTF = 0x0000000009D4A768


class WorldNtfMethod(IntEnum):
    SYNC_NEAR_ENTITIES = 0x00000006
    SYNC_CONTAINER_DATA = 0x00000015
    SYNC_CONTAINER_DIRTY_DATA = 0x00000016
    SYNC_SERVER_TIME = 0x0000002B
    SYNC_NEAR_DELTA_INFO = 0x0000002D
    SYNC_TO_ME_DELTA_INFO = 0x0000002E


class ChitChatNtfMethod(IntEnum):
    NOTIFY_NEWEST_CHIT_CHAT_MSGS = 0x00000001


def get_message_type_name(msg_type: int) -> str:
    try:
        return MessageType(msg_type).name
    except ValueError:
        return f"UNKNOWN_{msg_type}"


def get_world_ntf_method_name(method_id: int) -> str:
    try:
        return WorldNtfMethod(method_id).name
    except ValueError:
        return f"UNKNOWN_METHOD_{method_id:08X}"


class ChitChatChannelType(IntEnum):
    Unknown = 0
    World = 1
    Current = 2
    Team = 3
    Guild = 4
    Private = 5
    Group = 6
    TopNotice = 7
    System = 99


__all__ = [
    "MessageType",
    "ServiceID",
    "WorldNtfMethod",
    "ChitChatNtfMethod",
    "get_message_type_name",
    "get_world_ntf_method_name",
]
