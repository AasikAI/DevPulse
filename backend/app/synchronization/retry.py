import random
from collections.abc import Callable

BASE_DELAY_SECONDS = 60
MAX_DELAY_SECONDS = 15 * 60
MAX_RETRIES = 5
# Longer rate-limit waits are not retried inside one task; the next scheduled run handles them.
RATE_LIMIT_RETRY_CEILING_SECONDS = MAX_DELAY_SECONDS


def retry_delay_seconds(
    retries_so_far: int,
    retry_after: int | None = None,
    rng: Callable[[], float] = random.random,
) -> int:
    """Seconds to wait before the next attempt.

    Normally exponential (60 s, 120 s, 240 s ... capped at 15 min) with jitter,
    so many failing jobs do not all retry at the same moment. When GitHub said
    how long to wait (rate limit), wait that long plus a little jitter.
    """
    if retry_after is not None:
        return min(retry_after, MAX_DELAY_SECONDS) + int(rng() * 30)
    ceiling = min(MAX_DELAY_SECONDS, BASE_DELAY_SECONDS * 2**retries_so_far)
    return int(ceiling / 2 + rng() * ceiling / 2)
