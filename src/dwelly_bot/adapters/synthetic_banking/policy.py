"""Reviewed observation queries shared by runtime projection and evaluation inputs."""

from functools import lru_cache

from pydantic import TypeAdapter

from dwelly_bot.resources import text


@lru_cache(maxsize=1)
def read_queries() -> dict[str, list[str]]:
    return TypeAdapter(dict[str, list[str]]).validate_json(
        text("adapters/synthetic_banking/read_queries.json")
    )


def is_observation(system: str, query: str) -> bool:
    """Unknown, mixed and command responses stay outside decision-time evidence."""
    return query in read_queries().get(system, [])
