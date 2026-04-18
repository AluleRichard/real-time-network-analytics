from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from app.database import engine, Base, get_db
from app.models import NetworkMetric
from app.schemas import NetworkMetricSchema
from app.collector import collect_metrics

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database initialized and tables created.")
    
    # Background collection task
    async def background_collector():
        while True:
            try:
                db = next(get_db())
                metric = collect_metrics(db)
                if metric:
                    schema = NetworkMetricSchema.model_validate(metric)
                    await manager.broadcast(schema.model_dump())
            except Exception as e:
                logger.error(f"Background error: {e}")
            await asyncio.sleep(30)  # every 30 seconds

    task = asyncio.create_task(background_collector())
    yield
    # Shutdown
    task.cancel()
    logger.info("Backend shutting down...")

app = FastAPI(lifespan=lifespan, title="Network Performance Analytics Dashboard")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the dashboard.html at root[](http://127.0.0.1:8000/)
@app.get("/", response_class=FileResponse)
async def serve_dashboard():
    return FileResponse("dashboard.html")

# Mount static files (for future CSS/JS/images if needed)
app.mount("/static", StaticFiles(directory="."), name="static")

# REST endpoints
@app.get("/metrics/latest", response_model=NetworkMetricSchema)
def get_latest_metrics(db: Session = Depends(get_db)):
    metric = db.query(NetworkMetric).order_by(NetworkMetric.timestamp.desc()).first()
    if metric:
        return metric
    return NetworkMetricSchema(timestamp=datetime.now(timezone.utc), packet_loss=0.0)

@app.get("/metrics/history", response_model=list[NetworkMetricSchema])
def get_history(db: Session = Depends(get_db), limit: int = 100):
    metrics = db.query(NetworkMetric).order_by(NetworkMetric.timestamp.desc()).limit(limit).all()
    return metrics[::-1]  # reverse to chronological order

# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Health check
@app.get("/health")
def health():
    return {"status": "healthy", "message": "Network Dashboard Backend is running"}