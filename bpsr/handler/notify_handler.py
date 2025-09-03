from __future__ import annotations

from ..logutil import get_logger
from ..parser.constants import ChitChatNtfMethod, ServiceID, WorldNtfMethod
from ..parser.message import NotifyMessage
from ..proto import enum_chit_chat_channel_type_pb2, serv_chit_chat_ntf_pb2
from . import register_notify_handler

logger = get_logger("WorldNtfHandlers")
chat_logger = get_logger("Chat")


@register_notify_handler(ServiceID.WORLD_NTF, WorldNtfMethod.SYNC_NEAR_ENTITIES)
def handle_sync_near_entities(message: NotifyMessage) -> None:
    direction = "client->server" if message.is_from_client else "server->client"
    payload_size = len(message.payload) if message.payload else 0

    logger.debug(f"[{direction}] SYNC_NEAR_ENTITIES: {payload_size} bytes")


@register_notify_handler(ServiceID.WORLD_NTF, WorldNtfMethod.SYNC_CONTAINER_DATA)
def handle_sync_container_data(message: NotifyMessage) -> None:
    direction = "client->server" if message.is_from_client else "server->client"
    payload_size = len(message.payload) if message.payload else 0

    logger.debug(f"[{direction}] SYNC_CONTAINER_DATA: {payload_size} bytes")


@register_notify_handler(ServiceID.WORLD_NTF, WorldNtfMethod.SYNC_CONTAINER_DIRTY_DATA)
def handle_sync_container_dirty_data(message: NotifyMessage) -> None:
    direction = "client->server" if message.is_from_client else "server->client"
    payload_size = len(message.payload) if message.payload else 0

    logger.debug(f"[{direction}] SYNC_CONTAINER_DIRTY_DATA: {payload_size} bytes")


@register_notify_handler(ServiceID.WORLD_NTF, WorldNtfMethod.SYNC_SERVER_TIME)
def handle_sync_server_time(message: NotifyMessage) -> None:
    direction = "client->server" if message.is_from_client else "server->client"
    payload_size = len(message.payload) if message.payload else 0

    logger.debug(f"[{direction}] SYNC_SERVER_TIME: {payload_size} bytes")


@register_notify_handler(ServiceID.WORLD_NTF, WorldNtfMethod.SYNC_NEAR_DELTA_INFO)
def handle_sync_near_delta_info(message: NotifyMessage) -> None:
    direction = "client->server" if message.is_from_client else "server->client"
    payload_size = len(message.payload) if message.payload else 0

    logger.debug(f"[{direction}] SYNC_NEAR_DELTA_INFO: {payload_size} bytes")


@register_notify_handler(ServiceID.WORLD_NTF, WorldNtfMethod.SYNC_TO_ME_DELTA_INFO)
def handle_sync_to_me_delta_info(message: NotifyMessage) -> None:
    direction = "client->server" if message.is_from_client else "server->client"
    payload_size = len(message.payload) if message.payload else 0

    logger.debug(f"[{direction}] SYNC_TO_ME_DELTA_INFO: {payload_size} bytes")


@register_notify_handler(ServiceID.CHIT_CHAT_NTF, ChitChatNtfMethod.NOTIFY_NEWEST_CHIT_CHAT_MSGS)
def handle_notify_newest_chit_chat_msgs(message: NotifyMessage) -> None:
    if not message.payload:
        raise ValueError("Payload is empty")

    msg = serv_chit_chat_ntf_pb2.ChitChatNtf.NotifyNewestChitChatMsgs()
    msg.ParseFromString(message.payload)
    msg = msg.vRequest
    chat_msg = msg.chatMsg
    char_info = chat_msg.sendCharInfo

    try:
        channel_name = enum_chit_chat_channel_type_pb2.ChitChatChannelType.Name(msg.channelType)
    except ValueError:
        channel_name = f"UNKNOWN({msg.channelType})"

    chat_logger.info(f"[{channel_name}] {char_info.name}({char_info.charID}): {chat_msg.msgInfo.msgText}")
