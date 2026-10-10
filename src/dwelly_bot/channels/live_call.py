"""Speech queues for call sessions that a real voice transport currently holds open."""

import threading


class LiveCalls:
    """The executor queues reply text here; the transport speaks it in the same call.

    Only sessions opened by the transport accept speech. A closed or unknown session
    rejects it, so a reply never silently becomes a callback or a different channel.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._queues: dict[str, list[str]] = {}

    def open(self, session_id: str) -> None:
        with self._lock:
            self._queues.setdefault(session_id, [])

    def close(self, session_id: str) -> None:
        with self._lock:
            self._queues.pop(session_id, None)

    def is_open(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._queues

    def say(self, session_id: str, message: str) -> bool:
        """Queue speech for an open session; False means nothing was queued."""
        with self._lock:
            queue = self._queues.get(session_id)
            if queue is None:
                return False
            queue.append(message)
            return True

    def take(self, session_id: str) -> tuple[str, ...]:
        """Remove and return the speech queued so far for this session."""
        with self._lock:
            queue = self._queues.get(session_id)
            if not queue:
                return ()
            spoken = tuple(queue)
            queue.clear()
            return spoken
