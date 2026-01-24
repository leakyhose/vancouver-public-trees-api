import redis
import os
from dotenv import load_dotenv
load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))   
REDIS_USERNAME = os.getenv("REDIS_USERNAME")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

r = redis.Redis(
    host=REDIS_HOST,
    port=int(REDIS_PORT),
    username=REDIS_USERNAME,
    password=REDIS_PASSWORD,
    decode_responses=True
)
success = r.set('foo', 'bar')
# True

result = r.get('foo')
print(result)
# >>> bar

