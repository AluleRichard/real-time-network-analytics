from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
import logging
from contextlib import asynccontextmanager
from app.database import get_db, Base, engine 
from app.models import NetworkMetric
from app.schemas import NetworkMetricSchema
from app.collector import collect_metrics
from datetime import datetime, timezone
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

#logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Global Websocket manager
class ConnectionManager:
    def __init__(self): 
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict): #dictionaries concept used here...
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass


manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    #Startup
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized and tables created.")

    #Background Collection Task
    async def background_collection():
        while True:
            try:
               db = next(get_db())
               metric = collect_metrics(db)
               if metric:
                   schema  = NetworkMetricSchema.model_validate(metric)
                   await manager.broadcast(schema.model_dump())
            except Exception as e:
                logger.error(f"Error in background collection: {e}")
            await asyncio.sleep(30)  # Collect every 30 seconds

    task = asyncio.create_task(background_collection())
    yield
    # Shutdown
    task.cancel()
    logger.info("Background collection task cancelled.")

app = FastAPI(lifespan=lifespan, title="Network Performance Analytics Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # will be Changed to my frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)   

app.mount("/static", StaticFiles(directory="."), name="static") 

@app.get("/", response_class=FileResponse)
async def serve_dashboard():
    return FileResponse("dashboard.html")

#REST endpoint - latest metrics 
@app.get("/metrics/latest", response_model=NetworkMetricSchema)
def get_latest_metrics(db: Session = Depends(get_db)):
    metric = db.query(NetworkMetric).order_by(NetworkMetric.timestamp.desc()).first()
    if metric: 
        return metric
    
    # Return empty with current UTC time if no data yet
    return NetworkMetricSchema(
        timestamp=datetime.now(timezone.utc),
        packet_loss=0.0
    )  

@app.get("/metrics/history", response_model=list[NetworkMetricSchema])
def get_history(db: Session = Depends(get_db), limit: int = 50):
    metrics = db.query(NetworkMetric).order_by(NetworkMetric.timestamp.desc()).limit(limit).all()
    return metrics[::-1]  # reverse to chronological order

#Websockets for real-time updates
@app.websocket("/ws")  #unencrypted websocket for simplicity, will be changed to secure wss in production
async def websocket_endpoints(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

#Health check
@app.get("/health")
def health():
    return {"status": "healthy", "message": "Network Performance Analytics Dashboard API is running."}