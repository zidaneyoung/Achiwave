from unittest.mock import MagicMock, patch

import pytest
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from achiwave_backend.config import Settings
from achiwave_backend.redis_client import (
    RedisUnavailableError,
    create_redis_client,
    ping_redis,
)


def test_create_redis_client_uses_configured_timeouts() -> None:
    settings = Settings(
        _env_file=None,
        redis_url="redis://localhost:6379/0",
        redis_connect_timeout_seconds=1.5,
        redis_socket_timeout_seconds=2.0,
    )

    with patch(
        "achiwave_backend.redis_client.Redis.from_url"
    ) as from_url:
        create_redis_client(settings)

    from_url.assert_called_once_with(
        "redis://localhost:6379/0",
        decode_responses=True,
        health_check_interval=30,
        socket_connect_timeout=1.5,
        socket_timeout=2.0,
    )


def test_ping_redis_returns_true() -> None:
    client = MagicMock(spec=Redis)
    client.ping.return_value = True

    assert ping_redis(client) is True


def test_ping_redis_raises_controlled_error() -> None:
    client = MagicMock(spec=Redis)
    client.ping.side_effect = RedisConnectionError("private-host:6379")

    with pytest.raises(RedisUnavailableError) as captured:
        ping_redis(client)

    assert str(captured.value) == "Redis is unavailable."
    assert "private-host" not in str(captured.value)
