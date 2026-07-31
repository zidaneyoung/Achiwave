from redis import Redis
from redis.exceptions import RedisError

from achiwave_backend.config import Settings


class RedisUnavailableError(RuntimeError):
    """Controlled dependency error that does not reveal connection details."""


def create_redis_client(settings: Settings) -> Redis:
    return Redis.from_url(
        settings.require_redis_url(),
        decode_responses=True,
        health_check_interval=30,
        socket_connect_timeout=settings.redis_connect_timeout_seconds,
        socket_timeout=settings.redis_socket_timeout_seconds,
    )


def ping_redis(client: Redis) -> bool:
    try:
        return bool(client.ping())
    except RedisError as error:
        raise RedisUnavailableError("Redis is unavailable.") from error
