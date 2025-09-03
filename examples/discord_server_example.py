#!/usr/bin/env python3
"""
Example Discord WebSocket server for testing BPSRLog integration.

This is a simple WebSocket server that receives chat messages from BPSRLog
and can forward them to Discord webhooks or log them locally.

Usage:
    python discord_server_example.py [--port 8080] [--webhook-url WEBHOOK_URL]
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime
from typing import Any

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    print("Please install websockets: pip install websockets")
    exit(1)


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DiscordServer")


class DiscordServer:
    """Simple WebSocket server for receiving BPSRLog chat messages."""

    def __init__(self, port: int = 8080, webhook_url: str | None = None):
        self.port = port
        self.webhook_url = webhook_url
        self.clients: set[WebSocketServerProtocol] = set()

    async def start(self) -> None:
        """Start the WebSocket server."""
        logger.info(f"Starting Discord WebSocket server on port {self.port}")

        async with websockets.serve(
            self.handle_client,
            "localhost",
            self.port,
            ping_interval=30,
            ping_timeout=10,
        ):
            logger.info(f"Discord WebSocket server listening on ws://localhost:{self.port}/ws")
            await asyncio.Future()  # Run forever

    async def handle_client(self, websocket: WebSocketServerProtocol) -> None:
        """Handle a new WebSocket client connection."""
        client_address = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"New client connected: {client_address}")

        self.clients.add(websocket)

        try:
            # Send authentication success message
            await websocket.send(json.dumps({"type": "auth_success", "message": "Connected to Discord server"}))

            async for message in websocket:
                await self.handle_message(websocket, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_address}")
        except Exception as e:
            logger.error(f"Error handling client {client_address}: {e}")
        finally:
            self.clients.discard(websocket)

    async def handle_message(self, websocket: WebSocketServerProtocol, message: str) -> None:
        """Handle a message from a WebSocket client."""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type == "chat_message":
                await self.handle_chat_message(data.get("data", {}))
            elif message_type == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def handle_chat_message(self, chat_data: dict[str, Any]) -> None:
        """Handle a chat message from BPSRLog."""
        try:
            timestamp = datetime.fromtimestamp(chat_data.get("timestamp", 0))
            channel_name = chat_data.get("channel_name", "UNKNOWN")
            character_name = chat_data.get("character_name", "Unknown")
            character_id = chat_data.get("character_id", "0")
            message_text = chat_data.get("message_text", "")

            # Log the chat message
            logger.info(f"[{timestamp:%H:%M:%S}] [{channel_name}] {character_name}({character_id}): {message_text}")

            # TODO: Forward to Discord webhook if configured
            if self.webhook_url:
                await self.forward_to_discord(chat_data)

        except Exception as e:
            logger.error(f"Error handling chat message: {e}")

    async def forward_to_discord(self, chat_data: dict[str, Any]) -> None:
        """Forward chat message to Discord webhook (placeholder implementation)."""
        # This is where you would implement Discord webhook integration
        # For now, just log that we would send it
        logger.info(f"Would forward to Discord: {chat_data.get('message_text', '')}")


def main():
    parser = argparse.ArgumentParser(description="Discord WebSocket Server for BPSRLog")
    parser.add_argument("--port", type=int, default=8080, help="WebSocket server port")
    parser.add_argument("--webhook-url", help="Discord webhook URL (optional)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    server = DiscordServer(port=args.port, webhook_url=args.webhook_url)

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")


if __name__ == "__main__":
    main()
