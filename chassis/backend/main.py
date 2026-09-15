import logging
import threading
from datetime import datetime
from fastapi import FastAPI
from mqtt_client import create_mqtt_client, set_message_handler
from database import engine, SessionLocal
from models import Base, Classification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(title="HazeGuard Backend")

mqtt_client = None


def save_classification(payload: dict):
    db = SessionLocal()
    try:
        record = Classification(
            node_id=payload["node_id"],
            timestamp=datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00")),
            signal_type=payload["signal_type"],
            confidence=payload["confidence"],
            lat=payload["coordinates"]["lat"],
            lon=payload["coordinates"]["lon"],
            metadata_json=payload.get("metadata"),
        )
        db.add(record)
        db.commit()
        logger.info(f"Saved classification for node {record.node_id}")
    except Exception as e:
        logger.error(f"Failed to save classification: {e}")
        db.rollback()
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    global mqtt_client
    Base.metadata.create_all(bind=engine)
    set_message_handler(save_classification)
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