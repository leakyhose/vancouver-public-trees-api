from functools import wraps
from redis_client import r
import json
import hashlib


def redis_cache(expire_seconds):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_data = {
                "func_name": func.__name__,
                "args": args,
                "kwargs": kwargs
            }
            
            cache_key = f"cache:{hashlib.md5(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()}"
            
            cached = r.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = func(**args, **kwargs)
            r.setex(cache_key, expire_seconds, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator
    

            

           