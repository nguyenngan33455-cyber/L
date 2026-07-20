"""Dashboard exceptions for ZBGym.

This module defines all custom exceptions used by the Dashboard Connector.
Each exception provides specific error information for debugging and handling.
"""

from __future__ import annotations


class DashboardError(Exception):
    """Base exception for all Dashboard-related errors.

    All other Dashboard exceptions inherit from this class.
    This allows catching any Dashboard error with a single except clause.

    Example:
        try:
            dashboard.connect(url, api_key)
        except DashboardError as e:
            logger.error(f"Dashboard error: {e}")
    """

    def __init__(self, message: str, details: dict | None = None) -> None:
        """Initialize DashboardError.

        Args:
            message: Human-readable error message.
            details: Optional dictionary with additional error context.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class DashboardConnectionError(DashboardError):
    """Raised when connection to Dashboard server fails.

    This exception indicates network-level failures such as:
    - Server unreachable
    - DNS resolution failure
    - Network timeout
    - SSL/TLS errors

    Example:
        try:
            dashboard.connect("https://dashboard.example.com", api_key)
        except DashboardConnectionError as e:
            logger.warning(f"Cannot connect to dashboard: {e}")
            # Fallback to local logging
    """

    def __init__(
        self,
        message: str = "Failed to connect to Dashboard server",
        url: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Initialize DashboardConnectionError.

        Args:
            message: Error message.
            url: The URL that failed to connect.
            reason: Underlying reason for the failure.
        """
        details = {}
        if url:
            details["url"] = url
        if reason:
            details["reason"] = reason
        super().__init__(message, details)


class DashboardTimeoutError(DashboardError):
    """Raised when Dashboard operation times out.

    This exception indicates that an operation took too long to complete.
    Common causes:
    - Slow network connection
    - Server overload
    - Request too large

    Example:
        try:
            dashboard.publish_metrics(metrics, timeout=5)
        except DashboardTimeoutError:
            logger.warning("Metrics publish timed out")
    """

    def __init__(
        self,
        message: str = "Dashboard operation timed out",
        operation: str | None = None,
        timeout: float | None = None,
    ) -> None:
        """Initialize DashboardTimeoutError.

        Args:
            message: Error message.
            operation: The operation that timed out.
            timeout: The timeout value in seconds.
        """
        details = {}
        if operation:
            details["operation"] = operation
        if timeout is not None:
            details["timeout"] = timeout
        super().__init__(message, details)


class DashboardAuthError(DashboardError):
    """Raised when Dashboard authentication fails.

    This exception indicates authentication failures such as:
    - Invalid API key
    - Expired API key
    - Missing API key
    - Insufficient permissions

    Example:
        try:
            dashboard.connect(api_key="invalid_key")
        except DashboardAuthError as e:
            logger.error(f"Authentication failed: {e}")
            sys.exit(1)
    """

    def __init__(
        self,
        message: str = "Dashboard authentication failed",
        api_key_masked: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Initialize DashboardAuthError.

        Args:
            message: Error message.
            api_key_masked: API key (should be masked for security).
            reason: Reason for authentication failure.
        """
        details = {}
        if api_key_masked:
            details["api_key"] = api_key_masked
        if reason:
            details["reason"] = reason
        super().__init__(message, details)


class DashboardProtocolError(DashboardError):
    """Raised when Dashboard protocol is violated.

    This exception indicates protocol-level errors such as:
    - Invalid packet format
    - Missing required fields
    - Invalid packet type
    - Malformed data

    Example:
        try:
            dashboard.send_packet(invalid_packet)
        except DashboardProtocolError as e:
            logger.error(f"Protocol error: {e}")
    """

    def __init__(
        self,
        message: str = "Dashboard protocol error",
        packet_type: str | None = None,
        field: str | None = None,
    ) -> None:
        """Initialize DashboardProtocolError.

        Args:
            message: Error message.
            packet_type: Type of packet that caused the error.
            field: Field that caused the error.
        """
        details = {}
        if packet_type:
            details["packet_type"] = packet_type
        if field:
            details["field"] = field
        super().__init__(message, details)


class DashboardUploadError(DashboardError):
    """Raised when file upload to Dashboard fails.

    This exception indicates upload failures such as:
    - File too large
    - Invalid file type
    - Network interruption during upload
    - Server rejection

    Example:
        try:
            dashboard.publish_checkpoint("/path/to/model.pt")
        except DashboardUploadError as e:
            logger.error(f"Upload failed: {e}")
    """

    def __init__(
        self,
        message: str = "Failed to upload to Dashboard",
        file_path: str | None = None,
        file_size: int | None = None,
        reason: str | None = None,
    ) -> None:
        """Initialize DashboardUploadError.

        Args:
            message: Error message.
            file_path: Path to the file that failed to upload.
            file_size: Size of the file in bytes.
            reason: Reason for the upload failure.
        """
        details = {}
        if file_path:
            details["file_path"] = file_path
        if file_size is not None:
            details["file_size"] = file_size
        if reason:
            details["reason"] = reason
        super().__init__(message, details)


class DashboardSessionError(DashboardError):
    """Raised when Dashboard session operation fails.

    This exception indicates session-related errors such as:
    - Session not found
    - Session already finished
    - Invalid session ID
    - Session creation failed

    Example:
        try:
            dashboard.finish_session(session_id="invalid")
        except DashboardSessionError as e:
            logger.error(f"Session error: {e}")
    """

    def __init__(
        self,
        message: str = "Dashboard session error",
        session_id: str | None = None,
        operation: str | None = None,
    ) -> None:
        """Initialize DashboardSessionError.

        Args:
            message: Error message.
            session_id: The session ID that caused the error.
            operation: The operation that failed.
        """
        details = {}
        if session_id:
            details["session_id"] = session_id
        if operation:
            details["operation"] = operation
        super().__init__(message, details)


class DashboardQueueFullError(DashboardError):
    """Raised when Dashboard internal queue is full.

    This exception indicates that the publish queue has reached
    its maximum capacity. This can happen when:
    - Network is slow
    - Too many metrics being published
    - Connection is down

    Example:
        try:
            dashboard.publish_metrics(large_batch)
        except DashboardQueueFullError:
            logger.warning("Dashboard queue full, dropping oldest")
    """

    def __init__(
        self,
        message: str = "Dashboard queue is full",
        queue_size: int | None = None,
        max_size: int | None = None,
    ) -> None:
        """Initialize DashboardQueueFullError.

        Args:
            message: Error message.
            queue_size: Current size of the queue.
            max_size: Maximum queue size.
        """
        details = {}
        if queue_size is not None:
            details["queue_size"] = queue_size
        if max_size is not None:
            details["max_size"] = max_size
        super().__init__(message, details)


class DashboardReconnectError(DashboardError):
    """Raised when Dashboard reconnection fails.

    This exception indicates that all reconnection attempts
    have failed. This typically happens when:
    - Server is down for extended period
    - Network infrastructure issues
    - Invalid configuration

    Example:
        try:
            dashboard.connect(reconnect=True)
        except DashboardReconnectError:
            logger.error("All reconnection attempts failed")
    """

    def __init__(
        self,
        message: str = "Failed to reconnect to Dashboard",
        attempts: int | None = None,
        last_error: str | None = None,
    ) -> None:
        """Initialize DashboardReconnectError.

        Args:
            message: Error message.
            attempts: Number of reconnection attempts made.
            last_error: Error message from the last attempt.
        """
        details = {}
        if attempts is not None:
            details["attempts"] = attempts
        if last_error:
            details["last_error"] = last_error
        super().__init__(message, details)
