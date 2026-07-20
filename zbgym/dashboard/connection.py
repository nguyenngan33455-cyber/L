"""Dashboard connection management for ZBGym.

This module handles WebSocket and HTTP connections to the Dashboard server,
including connection pooling, reconnection with exponential backoff,
heartbeat, and error handling.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from queue import Empty, Queue
from typing import Any, Callable
from urllib.parse import urlparse

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketClientProtocol = Any

import requests

from zbgym.dashboard.config import DashboardConfig
from zbgym.dashboard.exceptions import (
    DashboardAuthError,
    DashboardConnectionError,
    DashboardReconnectError,
    DashboardTimeoutError,
)
from zbgym.dashboard.models import PacketType
from zbgym.dashboard.packet import Packet


logger = logging.getLogger(__name__)


class ConnectionState:
    """Connection state enum."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class DashboardConnection:
    """Manages connection to Dashboard server.

    This class handles WebSocket and HTTP connections with:
    - Automatic reconnection with exponential backoff
    - Heartbeat to keep connection alive
    - Request queuing during disconnection
    - Thread-safe operation

    Args:
        config: Dashboard configuration.
        on_connect: Callback when connected.
        on_disconnect: Callback when disconnected.
        on_error: Callback when error occurs.
    """

    def __init__(
        self,
        config: DashboardConfig,
        on_connect: Callable[[], None] | None = None,
        on_disconnect: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        """Initialize connection manager.

        Args:
            config: Dashboard configuration.
            on_connect: Callback on successful connect.
            on_disconnect: Callback on disconnect.
            on_error: Callback on error.
        """
        self.config = config
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._on_error = on_error

        # Connection state
        self._state = ConnectionState.DISCONNECTED
        self._state_lock = threading.Lock()

        # WebSocket
        self._ws: WebSocketClientProtocol | None = None
        self._ws_thread: threading.Thread | None = None
        self._ws_running = threading.Event()

        # Heartbeat
        self._heartbeat_thread: threading.Thread | None = None
        self._heartbeat_running = threading.Event()
        self._last_heartbeat: float = 0

        # Reconnection
        self._reconnect_attempts = 0
        self._reconnect_thread: threading.Thread | None = None
        self._should_reconnect = threading.Event()

        # Message queue
        self._send_queue: Queue[Packet | None] = Queue(maxsize=config.max_queue_size)
        self._worker_thread: threading.Thread | None = None

        # Callbacks
        self._callbacks: dict[str, list[Callable[[Any], None]]] = {
            "packet": [],
            "ack": [],
            "error": [],
        }

    @property
    def state(self) -> str:
        """Get current connection state."""
        with self._state_lock:
            return self._state

    @property
    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self.state == ConnectionState.CONNECTED

    def connect(self) -> None:
        """Connect to Dashboard server.

        Raises:
            DashboardConnectionError: If connection fails.
        """
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("websockets not available, using HTTP fallback")
            self._connect_http()
            return

        with self._state_lock:
            if self._state == ConnectionState.CONNECTED:
                return
            if self._state == ConnectionState.CONNECTING:
                return

            self._state = ConnectionState.CONNECTING

        try:
            self._connect_websocket()
            self._start_workers()
            self._set_state(ConnectionState.CONNECTED)
            self._reconnect_attempts = 0

            if self._on_connect:
                self._on_connect()

        except Exception as e:
            self._set_state(ConnectionState.DISCONNECTED)
            raise DashboardConnectionError(
                f"Failed to connect to {self.config.url}: {e}",
                url=self.config.url,
                reason=str(e),
            )

    def _connect_websocket(self) -> None:
        """Establish WebSocket connection."""
        ws_url = self.config.ws_url_computed

        # Add API key to headers
        headers = {}
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        logger.info(f"Connecting to WebSocket: {ws_url}")

        # Run connection in thread to allow timeout
        result = self._run_with_timeout(
            websockets.connect,
            ws_url,
            extra_headers=headers,
        )

        if result is None:
            raise DashboardTimeoutError(
                "Connection timeout",
                operation="websocket_connect",
                timeout=self.config.timeout,
            )

        self._ws = result

    def _connect_http(self) -> None:
        """HTTP fallback for when websockets unavailable."""
        # Test HTTP connection
        try:
            response = requests.get(
                f"{self.config.url}/health",
                timeout=self.config.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise DashboardConnectionError(
                f"HTTP health check failed: {e}",
                url=self.config.url,
                reason=str(e),
            )

    def _run_with_timeout(
        self,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any | None:
        """Run function with timeout.

        Args:
            func: Function to run.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Function result or None if timeout.
        """
        result = [None]
        exception = [None]

        def target() -> None:
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=self.config.timeout)

        if thread.is_alive():
            return None

        if exception[0]:
            raise exception[0]

        return result[0]

    def disconnect(self) -> None:
        """Disconnect from Dashboard server."""
        logger.info("Disconnecting from Dashboard")

        self._should_reconnect.clear()

        # Stop workers
        self._ws_running.clear()
        self._heartbeat_running.clear()

        # Send stop signal to queue
        self._send_queue.put(None)

        # Join threads
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2.0)

        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=2.0)

        # Close WebSocket
        if self._ws:
            try:
                import asyncio

                asyncio.run(self._ws.close())
            except Exception:
                pass
            self._ws = None

        self._set_state(ConnectionState.DISCONNECTED)

        if self._on_disconnect:
            self._on_disconnect()

    def reconnect(self) -> None:
        """Attempt to reconnect to server.

        Uses exponential backoff between attempts.

        Raises:
            DashboardReconnectError: If all reconnection attempts fail.
        """
        if not self.config.reconnect:
            raise DashboardReconnectError("Reconnection disabled in config")

        self._set_state(ConnectionState.RECONNECTING)
        self._should_reconnect.set()

        while self._should_reconnect.is_set():
            self._reconnect_attempts += 1

            if (
                self._reconnect_attempts > self.config.max_reconnect_attempts
                and self.config.max_reconnect_attempts > 0
            ):
                self._set_state(ConnectionState.FAILED)
                raise DashboardReconnectError(
                    f"Max reconnection attempts ({self.config.max_reconnect_attempts}) reached",
                    attempts=self._reconnect_attempts,
                    last_error="Max attempts exceeded",
                )

            # Calculate delay with exponential backoff
            delay = min(
                self.config.reconnect_delay
                * (self.config.reconnect_multiplier ** (self._reconnect_attempts - 1)),
                self.config.max_reconnect_delay,
            )

            logger.info(
                f"Reconnection attempt {self._reconnect_attempts}, "
                f"waiting {delay:.1f}s"
            )

            time.sleep(delay)

            try:
                self._connect_websocket()
                self._start_workers()
                self._set_state(ConnectionState.CONNECTED)
                self._reconnect_attempts = 0

                logger.info("Reconnection successful")

                if self._on_connect:
                    self._on_connect()

                return

            except Exception as e:
                logger.warning(f"Reconnection attempt failed: {e}")

                if self._on_error:
                    self._on_error(e)

        self._set_state(ConnectionState.DISCONNECTED)

    def send(self, packet: Packet) -> None:
        """Send packet to server.

        If not connected, packet is queued.

        Args:
            packet: Packet to send.
        """
        if self._send_queue.full():
            logger.warning("Send queue full, dropping packet")
            return

        self._send_queue.put(packet)

    def send_now(self, packet: Packet) -> None:
        """Send packet immediately, blocking.

        Args:
            packet: Packet to send.

        Raises:
            DashboardConnectionError: If not connected or send fails.
        """
        if not self.is_connected:
            raise DashboardConnectionError("Not connected to server")

        try:
            self._send_ws(packet)
        except Exception as e:
            raise DashboardConnectionError(
                f"Failed to send packet: {e}",
                reason=str(e),
            )

    def _send_ws(self, packet: Packet) -> None:
        """Send packet via WebSocket."""
        if not self._ws:
            return

        import asyncio

        try:
            asyncio.run(self._ws.send(packet.to_json()))
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")
            raise

    def _start_workers(self) -> None:
        """Start background worker threads."""
        # Send worker
        self._ws_running.set()
        self._worker_thread = threading.Thread(
            target=self._send_worker,
            daemon=True,
            name="DashboardSendWorker",
        )
        self._worker_thread.start()

        # Heartbeat worker
        self._heartbeat_running.set()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_worker,
            daemon=True,
            name="DashboardHeartbeat",
        )
        self._heartbeat_thread.start()

    def _send_worker(self) -> None:
        """Background worker that sends queued packets."""
        import asyncio

        while self._ws_running.is_set():
            try:
                packet = self._send_queue.get(timeout=1.0)

                if packet is None:
                    break

                if self.is_connected and self._ws:
                    try:
                        asyncio.run(self._ws.send(packet.to_json()))
                    except Exception as e:
                        logger.error(f"Send error: {e}")
                        self._handle_send_error(e)
                else:
                    # Re-queue if not connected
                    if not self._send_queue.full():
                        self._send_queue.put(packet)

            except Empty:
                continue
            except Exception as e:
                logger.error(f"Send worker error: {e}")

    def _heartbeat_worker(self) -> None:
        """Background worker that sends heartbeats."""
        while self._heartbeat_running.is_set():
            time.sleep(self.config.heartbeat_interval)

            if not self.is_connected:
                continue

            self._last_heartbeat = time.time()

            heartbeat = Packet(
                type=PacketType.HEARTBEAT,
                session="",
                payload={"timestamp": self._last_heartbeat},
            )

            try:
                self.send(heartbeat)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    def _handle_send_error(self, error: Exception) -> None:
        """Handle send error and potentially reconnect."""
        logger.warning(f"Send error, will attempt reconnect: {error}")

        if self.config.reconnect:
            thread = threading.Thread(
                target=self.reconnect,
                daemon=True,
            )
            thread.start()
        else:
            self._set_state(ConnectionState.DISCONNECTED)

    def _set_state(self, state: str) -> None:
        """Set connection state thread-safely."""
        with self._state_lock:
            old_state = self._state
            self._state = state

            if old_state != state:
                logger.debug(f"Connection state: {old_state} -> {state}")

    def on_packet(self, callback: Callable[[dict], None]) -> None:
        """Register packet callback.

        Args:
            callback: Function to call with received packets.
        """
        self._callbacks["packet"].append(callback)

    def upload_file(
        self,
        file_path: str,
        file_data: bytes,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """Upload file to server.

        Args:
            file_path: Original file path.
            file_data: File content bytes.
            metadata: File metadata.

        Returns:
            Server response.

        Raises:
            DashboardConnectionError: If upload fails.
            DashboardUploadError: If server rejects upload.
        """
        if not self.is_connected:
            raise DashboardConnectionError("Not connected to server")

        # Prepare multipart request
        url = f"{self.config.url}/upload"
        files = {"file": (file_path, file_data)}
        data = {"metadata": json.dumps(metadata)}

        headers = {}
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        try:
            response = requests.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=60,  # Longer timeout for uploads
            )
            response.raise_for_status()
            return response.json()

        except requests.Timeout:
            raise DashboardTimeoutError(
                "File upload timed out",
                operation="upload",
                timeout=60,
            )
        except requests.RequestException as e:
            raise DashboardConnectionError(
                f"File upload failed: {e}",
                reason=str(e),
            )

    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return self._send_queue.qsize()

    @property
    def reconnect_attempts(self) -> int:
        """Get number of reconnection attempts."""
        return self._reconnect_attempts

    def __enter__(self) -> "DashboardConnection":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.disconnect()
