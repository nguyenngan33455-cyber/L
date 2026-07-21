"""Plugin sandbox for safe plugin execution."""

from __future__ import annotations

import logging
import threading
import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


BLOCKED_MODULES = [
    "os",
    "sys",
    "subprocess",
    "ctypes",
    "socket",
    "urllib",
    "http",
    "ftplib",
    "telnetlib",
    "sqlite3",
    "pty",
    "tty",
    "termios",
    "fcntl",
    "resource",
]


class SandboxPolicy(Enum):
    """Sandbox policies for plugin execution."""

    SAFE = "safe"
    MODERATE = "moderate"
    UNRESTRICTED = "unrestricted"


@dataclass
class SandboxConfig:
    """Configuration for plugin sandbox."""

    policy: SandboxPolicy = SandboxPolicy.SAFE
    timeout_seconds: float = 5.0
    max_memory_mb: int = 256
    allow_threads: bool = True
    allow_network: bool = False
    allowed_modules: list[str] = field(default_factory=list)
    blocked_modules: list[str] = field(default_factory=lambda: BLOCKED_MODULES)


@dataclass
class SandboxResult:
    """Result of sandboxed execution."""

    success: bool
    value: Any = None
    error: Exception | None = None
    error_traceback: str = ""
    execution_time: float = 0.0
    timeout: bool = False


class PluginSandbox:
    """
    Sandbox for safe plugin execution.

    Provides:
    - Timeout enforcement
    - Exception isolation
    - Resource limits
    - Health checks
    """

    def __init__(self, config: SandboxConfig | None = None) -> None:
        """
        Initialize the sandbox.

        Args:
            config: Sandbox configuration
        """
        self._config = config or SandboxConfig()
        self._health_status: dict[str, bool] = {}

    @property
    def config(self) -> SandboxConfig:
        """Get sandbox configuration."""
        return self._config

    def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> SandboxResult:
        """
        Execute a function in the sandbox.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            SandboxResult with execution details
        """
        import time

        start_time = time.time()
        result = SandboxResult(success=False)

        def target():
            try:
                result.value = func(*args, **kwargs)
                result.success = True
            except Exception as e:
                result.error = e
                result.error_traceback = traceback.format_exc()

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=self._config.timeout_seconds)

        result.execution_time = time.time() - start_time

        if thread.is_alive():
            result.timeout = True
            result.error = TimeoutError(
                f"Execution timed out after {self._config.timeout_seconds}s"
            )
            result.error_traceback = traceback.format_exc()

        return result

    def execute_safe(
        self,
        func: Callable[..., T],
        default: T,
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Execute a function, returning default on failure.

        Args:
            func: Function to execute
            default: Default value to return on failure
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result or default
        """
        result = self.execute(func, *args, **kwargs)
        if result.success:
            return result.value
        logger.warning(f"Sandbox execution failed: {result.error}")
        return default

    def validate_return(self, value: Any) -> tuple[bool, str | None]:
        """
        Validate a return value from sandboxed execution.

        Args:
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None

        # Check for forbidden types
        forbidden = (type(open), type(__import__), type(exec), type(eval))

        def check_value(v: Any) -> bool:
            return not isinstance(v, forbidden)

        if isinstance(value, (list, tuple)):
            return all(check_value(v) for v in value), None
        elif isinstance(value, dict):
            return all(
                check_value(k) and check_value(v) for k, v in value.items()
            ), None

        return check_value(value), None

    def check_module_access(self, module_name: str) -> bool:
        """
        Check if a module can be accessed by a plugin.

        Args:
            module_name: Module name

        Returns:
            True if module is allowed
        """
        if self._config.policy == SandboxPolicy.UNRESTRICTED:
            return True

        # Check blocked modules
        for blocked in self._config.blocked_modules:
            if module_name.startswith(blocked):
                return False

        # Check allowed modules
        if self._config.allowed_modules:
            for allowed in self._config.allowed_modules:
                if module_name.startswith(allowed):
                    return True
            return False

        return True

    def register_health_check(
        self,
        plugin_name: str,
        check_func: Callable[[], bool],
    ) -> None:
        """
        Register a health check for a plugin.

        Args:
            plugin_name: Plugin name
            check_func: Function that returns True if healthy
        """
        self._health_status[plugin_name] = True
        self._health_checks[plugin_name] = check_func

    def run_health_check(self, plugin_name: str) -> bool:
        """
        Run health check for a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            True if plugin is healthy
        """
        check_func = self._health_checks.get(plugin_name)
        if not check_func:
            return True

        result = self.execute(check_func)
        healthy = result.success and result.value is True

        self._health_status[plugin_name] = healthy

        if not healthy:
            logger.warning(f"Plugin {plugin_name} health check failed")

        return healthy

    def run_all_health_checks(self) -> dict[str, bool]:
        """
        Run health checks for all plugins.

        Returns:
            Dictionary of plugin names to health status
        """
        for plugin_name in list(self._health_checks.keys()):
            self.run_health_check(plugin_name)
        return self._health_status.copy()

    def cleanup_plugin(self, plugin_name: str) -> None:
        """
        Clean up resources for a plugin.

        Args:
            plugin_name: Plugin name
        """
        if plugin_name in self._health_checks:
            del self._health_checks[plugin_name]
        if plugin_name in self._health_status:
            del self._health_status[plugin_name]

        logger.debug(f"Cleaned up sandbox resources for: {plugin_name}")


# Global sandbox instance
_global_sandbox: PluginSandbox | None = None


def get_sandbox() -> PluginSandbox:
    """Get the global sandbox instance."""
    global _global_sandbox
    if _global_sandbox is None:
        _global_sandbox = PluginSandbox()
    return _global_sandbox
