import redis
from dotenv import load_dotenv
import os

load_dotenv()

HOST = os.getenv("REDIS_HOST")
PORT =os.getenv("REDIS_PORT")
CHANNEL = os.getenv("REDIS_CHANNEL")

redis_client = redis.Redis(host=HOST, port=int(PORT))
# redis_client.publish(CHANNEL, "DOWNLOAD FINISHED")
redis_client.publish(CHANNEL, "START DOWNLOAD")