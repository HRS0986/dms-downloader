from dotenv import load_dotenv
import os
import requests
from requests.auth import HTTPBasicAuth
import xmltodict
from tqdm import tqdm
import redis

load_dotenv()

USERNAME=os.getenv("DMS_USERNAME")
PASSWORD=os.getenv("DMS_PASSWORD")
DMS_URL=os.getenv("DMS_URL")
CHANNEL = os.getenv("REDIS_CHANNEL")
HOST = os.getenv("REDIS_HOST")
PORT = int(os.getenv("REDIS_PORT"))

redis_client = redis.Redis(host=HOST, port=PORT)

def remove_file(url :str):
    response = requests.delete(url, stream=True, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    print(response)


def download_file(url: str, filepath: str):
    response = requests.get(url, stream=True, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    total_size = int(response.headers.get('content-length', 0))
    progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)
    
    with open(filepath, "wb") as f:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            progress_bar.update(size)
    
    progress_bar.close()
    print("File downloaded to " + filepath)


def get_file_list() -> list[str]:
    headers = {
        "Depth": "1",
        "Content-Type": "application/xml"
    }
    response = requests.request("PROPFIND", DMS_URL, auth=HTTPBasicAuth(USERNAME, PASSWORD), headers=headers)
    if response.status_code == 207:
        data_dict = xmltodict.parse(response.text)
        file_list = []
        files = data_dict["d:multistatus"]["d:response"]
        for file_data in files:
            try:
                file_name = file_data["d:href"].split("/")[-1]
                if file_name != "":
                    file_list.append(file_name)
            except Exception as e:
                pass
        return file_list
    else:
        raise Exception("Error getting file list")


def send_notification(message: str, channel: str = 'my_channel'):
    redis_client.publish(channel, message)


def start_download():
    file_list = get_file_list()
    for file in file_list:
        print(file)
        download_file(DMS_URL + file, file)
        remove_file(DMS_URL + file)
    send_notification("DOWNLOAD FINISHED", CHANNEL)