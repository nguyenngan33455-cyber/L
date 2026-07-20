"""Dashboard authentication for ZBGym.

This module handles API key authentication with the Dashboard server.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from zbgym.dashboard.config import DashboardConfig
from zbgym.dashboard.exceptions import DashboardAuthError, DashboardConnectionError


logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication with Dashboard server.

    This class handles:
    - API key validation
    - Token refresh (if supported)
    - Authentication error handling

    Args:
        config: Dashboard configuration with API key.
    """

    def __init__(self, config: DashboardConfig) -> None:
        """Initialize auth manager.

        Args:
            config: Dashboard configuration.
        """
        self._config = config
        self._authenticated = False
        self._auth_token: str | None = None

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated.

        Returns:
            True if authenticated, False otherwise.
        """
        return self._authenticated

    def authenticate(self) -> None:
        """Authenticate with Dashboard server.

        Sends API key to server for validation.

        Raises:
            DashboardAuthError: If authentication fails.
            DashboardConnectionError: If cannot connect to server.
        """
        if not self._config.api_key:
            raise DashboardAuthError(
                "No API key provided",
                reason="api_key_missing",
            )

        try:
            response = self._validate_api_key(self._config.api_key)

            if response.get("success"):
                self._authenticated = True
                self._auth_token = response.get("token")
                logger.info(
                    f"Authenticated with Dashboard "
                    f"(key: {self._config.masked_api_key()})"
                )
            else:
                reason = response.get("error", "Invalid response")
                raise DashboardAuthError(
                    f"Authentication failed: {reason}",
                    api_key_masked=self._config.masked_api_key(),
                    reason=reason,
                )

        except requests.RequestException as e:
            raise DashboardConnectionError(
                f"Failed to connect to Dashboard for authentication: {e}",
                url=self._config.url,
                reason=str(e),
            )

    def _validate_api_key(self, api_key: str) -> dict[str, Any]:
        """Validate API key with server.

        Args:
            api_key: API key to validate.

        Returns:
            Server response dictionary.

        Raises:
            DashboardConnectionError: If request fails.
        """
        # Try auth endpoint first
        url = f"{self._config.url}/auth/validate"

        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                timeout=self._config.timeout,
            )

            if response.status_code == 401:
                raise DashboardAuthError(
                    "Invalid API key",
                    api_key_masked=self._mask_key(api_key),
                    reason="invalid_key",
                )

            if response.status_code == 403:
                raise DashboardAuthError(
                    "API key forbidden",
                    api_key_masked=self._mask_key(api_key),
                    reason="forbidden",
                )

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            # If auth endpoint doesn't exist, try health endpoint
            if isinstance(e, requests.HTTPError) and e.response.status_code in (
                404,
                405,
            ):
                logger.debug("Auth endpoint not found, checking health endpoint")
                return self._check_health_auth(api_key)

            raise

    def _check_health_auth(self, api_key: str) -> dict[str, Any]:
        """Fallback auth via health endpoint.

        Args:
            api_key: API key to check.

        Returns:
            Success response if key appears valid.
        """
        try:
            response = requests.get(
                f"{self._config.url}/health",
                headers={"X-API-Key": api_key},
                timeout=self._config.timeout,
            )

            if response.status_code == 200:
                # Health check passed, assume auth is ok
                return {"success": True, "token": None}

            return {"success": False, "error": "Authentication failed"}

        except requests.RequestException as e:
            raise DashboardConnectionError(
                f"Health check failed: {e}",
                url=self._config.url,
                reason=str(e),
            )

    def _mask_key(self, key: str) -> str:
        """Mask API key for logging.

        Args:
            key: API key to mask.

        Returns:
            Masked key showing first and last 4 chars.
        """
        if not key:
            return "None"
        if len(key) <= 8:
            return "*" * len(key)
        return f"{key[:4]}...{key[-4:]}"

    def logout(self) -> None:
        """Logout and clear authentication state."""
        self._authenticated = False
        self._auth_token = None
        logger.info("Logged out from Dashboard")

    def get_headers(self) -> dict[str, str]:
        """Get authentication headers for requests.

        Returns:
            Dictionary of headers including auth.
        """
        headers: dict[str, str] = {}

        if self._config.api_key:
            headers["X-API-Key"] = self._config.api_key

        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"

        return headers

    def require_auth(self) -> None:
        """Ensure authentication before proceeding.

        Raises:
            DashboardAuthError: If not authenticated.
        """
        if not self._authenticated:
            raise DashboardAuthError(
                "Not authenticated with Dashboard",
                reason="not_authenticated",
            )

    def __repr__(self) -> str:
        """String representation."""
        auth_status = "authenticated" if self._authenticated else "not authenticated"
        return f"AuthManager({auth_status}, key={self._config.masked_api_key()})"


def validate_api_key(api_key: str, url: str, timeout: float = 10.0) -> bool:
    """Validate an API key without creating a full client.

    Args:
        api_key: API key to validate.
        url: Dashboard server URL.
        timeout: Request timeout in seconds.

    Returns:
        True if API key is valid.

    Raises:
        DashboardAuthError: If key is invalid.
        DashboardConnectionError: If cannot connect to server.

    Example:
        if validate_api_key("zb_xxx", "https://dashboard.zbgym.dev"):
            print("API key is valid!")
    """
    config = DashboardConfig(url=url, api_key=api_key, timeout=timeout)
    auth = AuthManager(config)

    try:
        auth.authenticate()
        return True
    except DashboardAuthError:
        return False
    except DashboardConnectionError:
        raise
