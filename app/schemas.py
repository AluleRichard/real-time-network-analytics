from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NetworkMetricSchema(BaseModel):
    timestamp: datetime
    download_mbps: Optional[float] = None
    upload_mbps: Optional[float] = None
    ping_ms: Optional[float] = None
    packet_loss: float = 0.0
    bytes_sent: int = 0
    bytes_recv: int = 0
    packets_sent: int = 0
    packets_recv: int = 0

    class Config:
        from_attributes = True