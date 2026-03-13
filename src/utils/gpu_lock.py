"""GPU task serialization via flock.

Ensures only one GPU-intensive task runs at a time across all sessions
(including shell scripts using script/gpu-lock.sh). Uses fcntl.flock on
a shared lockfile -- automatic cleanup on crash/kill.

Usage::

    from src.utils.gpu_lock import GpuLock, gpu_lock, gpu_lock_status

    # As context manager
    with GpuLock():
        train_model(config)

    # As decorator
    @GpuLock()
    def train_model(config):
        ...

    # Convenience function
    with gpu_lock():
        train_model(config)

    # Check status
    status = gpu_lock_status()
    print(status)  # {"locked": False, "pid": None, "cmd": None}
"""

from __future__ import annotations

import fcntl
import functools
import os
import subprocess
import sys
from typing import Any, Callable, Optional

GPU_LOCKFILE = "/tmp/gpu-task.lock"


class GpuLock:
    """Exclusive GPU lock using flock on a shared lockfile.

    Compatible with ``script/gpu-lock.sh`` -- both use the same lockfile
    so shell and Python locks are mutually exclusive.

    Parameters
    ----------
    timeout : float | None
        Not directly supported by flock. If set, a warning is printed.
        Default is None (block forever until lock is acquired).
    """

    def __init__(self, timeout: Optional[float] = None) -> None:
        self.timeout = timeout
        self._fd: Optional[int] = None

    def __enter__(self) -> "GpuLock":
        if self.timeout is not None:
            print(
                "[gpu-lock] Warning: timeout is not supported with flock. "
                "Will block until lock is acquired.",
                file=sys.stderr,
            )

        # Open lockfile (create if needed)
        self._fd = os.open(GPU_LOCKFILE, os.O_WRONLY | os.O_CREAT, 0o666)

        print(
            f"[gpu-lock] Waiting for GPU lock...",
            file=sys.stderr,
        )
        # Acquire exclusive lock (blocking)
        fcntl.flock(self._fd, fcntl.LOCK_EX)
        print(
            f"[gpu-lock] Acquired GPU lock (PID {os.getpid()})",
            file=sys.stderr,
        )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._fd is not None:
            # Release lock and close fd
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
            self._fd = None
            print("[gpu-lock] Released GPU lock", file=sys.stderr)

    def __call__(self, func: Callable) -> Callable:
        """Use GpuLock as a decorator."""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with GpuLock(timeout=self.timeout):
                return func(*args, **kwargs)

        return wrapper


def gpu_lock() -> GpuLock:
    """Convenience function returning a GpuLock instance.

    Usage::

        with gpu_lock():
            train_model(config)
    """
    return GpuLock()


def gpu_lock_status() -> dict[str, Any]:
    """Check if the GPU lock is currently held.

    Returns
    -------
    dict
        ``{"locked": bool, "pid": int | None, "cmd": str | None}``
    """
    result: dict[str, Any] = {"locked": False, "pid": None, "cmd": None}

    try:
        fd = os.open(GPU_LOCKFILE, os.O_WRONLY | os.O_CREAT, 0o666)
    except OSError:
        return result

    try:
        # Try non-blocking lock
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Got it -- lock was free. Release immediately.
        fcntl.flock(fd, fcntl.LOCK_UN)
        result["locked"] = False
    except BlockingIOError:
        # Lock is held by another process
        result["locked"] = True

        # Try to find the holding PID via fuser
        try:
            out = subprocess.check_output(
                ["fuser", GPU_LOCKFILE],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
            if out:
                # fuser returns space-separated PIDs
                pid = int(out.split()[0])
                result["pid"] = pid
                # Get command line
                try:
                    cmd_out = subprocess.check_output(
                        ["ps", "-p", str(pid), "-o", "cmd", "--no-headers"],
                        stderr=subprocess.DEVNULL,
                        text=True,
                    ).strip()
                    result["cmd"] = cmd_out
                except (subprocess.CalledProcessError, OSError):
                    pass
        except (subprocess.CalledProcessError, OSError, ValueError):
            pass
    finally:
        os.close(fd)

    return result
