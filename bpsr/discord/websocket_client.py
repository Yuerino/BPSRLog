from __future__ import annotations

import asyncio
import json
import queue
import threading
from dataclasses import asdict, dataclass
from typing import Any

import websockets
from websockets import WebSocketClientProtocol

from ..logutil import get_logger

logger = get_logger("DiscordWebSocket")


@dataclass(slots=True)
class ChatMessage:
    timestamp: int
    channel_type: int
    channel_name: str
    character_id: str
    character_name: str
    message_text: str


@dataclass(slots=True)
class DiscordConfig:
    websocket_url: str
    jwt_token: str | None = None
    reconnect_delay: float = 5.0
    ping_interval: float = 30.0
    max_retries: int = 10


class DiscordWebSocketClient:
    def __init__(self, config: DiscordConfig) -> None:
        self.config = config
        self.message_queue: queue.Queue[ChatMessage] = queue.Queue()
        self.websocket: WebSocketClientProtocol | None = None
        self.running = False
        self.thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._retry_count = 0

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            logger.warning("WebSocket client is already running")
            return

        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
        logger.info("Discord WebSocket client started")

    def stop(self) -> None:
        if not self.running:
            return

        logger.info("Stopping Discord WebSocket client...")
        self.running = False
        self._stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
            if self.thread.is_alive():
                logger.warning("WebSocket thread did not stop gracefully")

        logger.info("Discord WebSocket client stopped")

    def send_chat_message(self, message: ChatMessage) -> None:
        if not self.running:
            logger.warning("Cannot send message: WebSocket client is not running")
            return

        try:
            self.message_queue.put_nowait(message)
        except queue.Full:
            logger.error("Message queue is full, dropping message")

    def update_jwt_token(self, token: str) -> None:
        self.config.jwt_token = token

    def _run_async_loop(self) -> None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._websocket_handler())
        except Exception as e:
            logger.error(f"Async loop error: {e}")
        finally:
            try:
                loop.close()
            except Exception:
                pass

    async def _websocket_handler(self) -> None:
        while self.running and not self._stop_event.is_set():
            try:
                await self._connect_and_run()
                self._retry_count = 0
            except Exception as e:
                self._retry_count += 1
                logger.error(f"WebSocket connection failed (attempt {self._retry_count}): {e}")

                if self._retry_count >= self.config.max_retries:
                    logger.error("Max retries reached, stopping WebSocket client")
                    break

                if not self._stop_event.is_set():
                    logger.info(f"Reconnecting in {self.config.reconnect_delay} seconds...")
                    await asyncio.sleep(self.config.reconnect_delay)

    async def _connect_and_run(self) -> None:
        logger.info(f"Connecting to Discord WebSocket: {self.config.websocket_url}")

        connect_kwargs = {
            "ping_interval": self.config.ping_interval,
        }

        if self.config.jwt_token:
            connect_kwargs["additional_headers"] = {"Authorization": f"Bearer {self.config.jwt_token}"}

        async with websockets.connect(self.config.websocket_url, **connect_kwargs) as websocket:
            self.websocket = websocket
            logger.info("Connected to Discord WebSocket")

            send_task = asyncio.create_task(self._send_messages())
            receive_task = asyncio.create_task(self._receive_messages())

            try:
                done, pending = await asyncio.wait([send_task, receive_task], return_when=asyncio.FIRST_COMPLETED)

                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            finally:
                self.websocket = None

    async def _send_messages(self) -> None:
        while self.running and not self._stop_event.is_set():
            try:
                message = await asyncio.get_event_loop().run_in_executor(None, self._get_message_with_timeout, 1.0)

                if message is None:
                    continue

                message_data = {"type": "chat_message", "data": asdict(message)}

                if self.websocket:
                    await self.websocket.send(json.dumps(message_data))
                    logger.debug(f"Sent chat message from {message.character_name}")

            except Exception as e:
                logger.error(f"Error sending message: {e}")
                break

    async def _receive_messages(self) -> None:
        while self.running and not self._stop_event.is_set():
            try:
                if not self.websocket:
                    break

                response = await self.websocket.recv()
                await self._handle_server_message(response)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed by server")
                break
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                break

    async def _handle_server_message(self, message: str) -> None:
        try:
            data = json.loads(message)
            message_type = data.get("type")
            logger.debug(f"Received message type: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from server: {message}")
        except Exception as e:
            logger.error(f"Error handling server message: {e}")

    def _get_message_with_timeout(self, timeout: float) -> ChatMessage | None:
        try:
            return self.message_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_status(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "connected": self.websocket is not None,
            "queue_size": self.message_queue.qsize(),
            "retry_count": self._retry_count,
            "thread_alive": self.thread.is_alive() if self.thread else False,
        }
