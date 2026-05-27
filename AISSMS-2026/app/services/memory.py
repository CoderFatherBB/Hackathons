import json
import redis
from app.core.config import settings

client = redis.Redis.from_url(settings.redis_url)

def add_exchange(conversation_id: str, role: str, content: str):
    key = f"conv:{conversation_id}"
    client.rpush(key, json.dumps({"role": role, "content": content}))
    client.ltrim(key, -10, -1)

def get_memory(conversation_id: str):
    key = f"conv:{conversation_id}"
    items = client.lrange(key, 0, -1)
    return [json.loads(i) for i in items]
