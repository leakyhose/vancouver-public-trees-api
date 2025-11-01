import os
import redis

redis_client = redis.Redis.from_url(
    os.environ["REDIS_URL"],
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)
