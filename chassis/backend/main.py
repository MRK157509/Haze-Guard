import logging
import threading
from fastapi import FastAPI
from mqtt_client import create_mqtt_client

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="HazeGuard Backend")

mqtt_client = None

@app.on_event("startup")
def startup_event():
    global mqtt_client
    mqtt_client = create_mqtt_client()
    thread = threading.Thread(target=mqtt_client.loop_forever, daemon=True)
    thread.start()

@app.on_event("shutdown")
def shutdown_event():
    if mqtt_client:
        mqtt_client.disconnect()

@app.get("/health")
def health_check():
    return {"status": "ok"} 