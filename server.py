import json
import os
from pathlib import Path
import asyncio
from typing import List

from fastapi import FastAPI, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import redis
from dotenv import load_dotenv

from models import ScraperConfig, ScrapedLink, ScrapeProgress
from r_queue import initialize
from scraper import scrape_with_progress

load_dotenv()

HOST = os.getenv("REDIS_HOST")
PORT = os.getenv("REDIS_PORT")
CHANNEL = os.getenv("REDIS_CHANNEL")
redis_client = redis.Redis(host=HOST, port=int(PORT))

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

config = {
    "save_path": ""
}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if (websocket in self.active_connections):
            self.active_connections.remove(websocket)

    async def send_progress(self, message: dict):
        # Create a copy of the connections list to avoid modification during iteration
        connections = self.active_connections.copy()
        disconnected_connections = []
        
        for connection in connections:
            try:
                await connection.send_json(message)
            except WebSocketDisconnect:
                # Track disconnected clients for removal
                disconnected_connections.append(connection)
            except Exception as e:
                print(f"Error sending message to WebSocket: {str(e)}")
                disconnected_connections.append(connection)
        
        # Remove any disconnected connections
        for conn in disconnected_connections:
            self.disconnect(conn)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/start")
def start_download(selected_links: list[ScrapedLink], background_tasks: BackgroundTasks):
    background_tasks.add_task(initialize, config["save_path"])
    redis_client.set("LINKS_TO_DOWNLOAD", json.dumps([link.model_dump_json() for link in selected_links]))
    redis_client.publish(CHANNEL, "START DOWNLOAD TO DMS")
    return {"status": "OK", "message": "URLs added to the queue"}

@app.get("/continue")
def continue_download():
    redis_client.publish(CHANNEL, "START LOCAL DOWNLOAD")
    return {"status": "OK", "message": "Continuing download from DMS"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Try to receive messages (ping-pong) to check if connection is still alive
            try:
                # Wait for a message with a timeout - prevents blocking indefinitely
                message = await asyncio.wait_for(websocket.receive_text(), timeout=10)
                # If client sends a message, you can handle it here
            except asyncio.TimeoutError:
                # No message received, but connection may still be alive
                # Send a ping to keep the connection open
                pass
            except WebSocketDisconnect:
                # Connection was closed by the client
                break
            
            # Sleep briefly to avoid CPU spinning
            await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
    finally:
        # Always make sure to remove the connection when done
        manager.disconnect(websocket)

@app.post("/scrape", response_model=list[ScrapedLink])
async def scrape_links(data: ScraperConfig, background_tasks: BackgroundTasks):
    config["save_path"] = data.save_path
    # Run the scraping process in a background task
    background_tasks.add_task(scrape_with_background, data.url, manager)
    return []  # Return empty array immediately, results will come via WebSocket

async def scrape_with_background(url: str, conn_manager: ConnectionManager):
    # This runs in the background and sends progress updates through the WebSocket
    async for progress in scrape_with_progress(url):
        await conn_manager.send_progress(progress)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
