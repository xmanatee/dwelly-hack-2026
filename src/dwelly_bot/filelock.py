"""Exclusive advisory file locks on POSIX (fcntl) and Windows (msvcrt)."""

from __future__ import annotations

import sys
import time
from typing import IO, Any

if sys.platform == "win32":
    import msvcrt

    def lock_exclusive(stream: IO[Any], *, blocking: bool = True) -> None:
        """Lock the first byte; raise BlockingIOError when non-blocking and already held."""
        stream.seek(0)
        while True:
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError as error:
                if not blocking:
                    raise BlockingIOError(str(error)) from error
                time.sleep(0.05)

else:
    import fcntl

    def lock_exclusive(stream: IO[Any], *, blocking: bool = True) -> None:
        """Hold an exclusive flock until the stream closes."""
        flags = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
        fcntl.flock(stream.fileno(), flags)
