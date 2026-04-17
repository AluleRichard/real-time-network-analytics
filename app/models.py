from sqlalchemy import Column, Float, BigInteger, DateTime
from datetime import datetime, timezone
from app.database import Base

class NetworkMetric(Base):
    __tablename__ = "network_metrics"

    timestamp = Column(
        DateTime, 
        primary_key=True, 
        default=lambda: datetime.now(timezone.utc)
    )
    download_mbps = Column(Float, nullable=True)
    upload_mbps = Column(Float, nullable=True)
    ping_ms = Column(Float, nullable=True)
    packet_loss = Column(Float, default=0.0)
    bytes_sent = Column(BigInteger, default=0)
    bytes_recv = Column(BigInteger, default=0)
    packets_sent = Column(BigInteger, default=0)
    packets_recv = Column(BigInteger, default=0)