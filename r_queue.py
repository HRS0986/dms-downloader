import redis
import os
from dotenv import load_dotenv
from main import start_download

load_dotenv()

HOST = os.getenv("REDIS_HOST")
PORT =os.getenv("REDIS_PORT")
CHANNEL = os.getenv("REDIS_CHANNEL")

redis_client = redis.Redis(host=HOST, port=int(PORT))
pubsub = redis_client.pubsub()
pubsub.subscribe(CHANNEL)


def initialize(save_path: str):
    print(f"Subscribed to {CHANNEL}. Waiting for messages...")
    for message in pubsub.listen():
        if message['type'] == 'message':
            data = message['data'].decode('utf-8')
            if data == "START LOCAL DOWNLOAD":
                start_download(save_path)
