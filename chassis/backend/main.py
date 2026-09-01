from fastapi import FastAPI

app = FastAPI(title="HazeGuard Backend")

@app.get("/health")
def health_check():
    return {"status": "ok"}
