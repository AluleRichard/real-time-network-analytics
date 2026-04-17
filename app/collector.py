import subprocess
import re 
import psutil
from pythonping import ping
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import NetworkMetric

def collect_metrics(db: Session): #receives a DB session to save collected metrics
    try:
        #ping (Latency and packet loss) - to google + cloudflare
        ping_results = ping('8.8.8.8', count = 4, timeout=2)
        ping_ms = ping_results.rtt_avg_ms
        success_rate = ping_results.success()
        packet_loss = (1  - success_rate) * 100

        #Speedtest (official CLI - Captured directly)
        speedtest_output = subprocess.check_output( 
            ["speedtest", "--simple"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=30
        )   
        download_mbps = re.search(r"Download:\s+([\d.]+)\s+Mbps", speedtest_output)
        upload_mbps = re.search(r"Upload:\s+([\d.]+)\s+Mbps", speedtest_output)

        download_mbps = float(download_mbps.group(1)) if download_mbps else None
        upload_mbps = float(upload_mbps.group(1)) if upload_mbps else None

        #Interface stats (psutil)
        net_io = psutil.net_io_counters(pernic=False)

        #Save to DB 
        metric = NetworkMetric(
            timestamp=datetime.now(timezone.utc),
            download_mbps=download_mbps,
            upload_mbps=upload_mbps,
            ping_ms=ping_ms,
            packet_loss=packet_loss,
            bytes_sent=net_io.bytes_sent,
            bytes_recv=net_io.bytes_recv,
            packets_sent=net_io.packets_sent,
            packets_recv=net_io.packets_recv
        )
        
        db.add(metric)
        db.commit()
        
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] "
              f"✅ Metric saved | Ping: {ping_ms:.1f}ms | Loss: {packet_loss:.1f}% | "
              f"↓ {download_mbps} Mbps | ↑ {upload_mbps} Mbps")
        
        return metric

    except subprocess.TimeoutExpired:
        print("❌ Speedtest timed out - skipping this cycle")
        db.rollback()
        return None
    except Exception as e:
        print(f"❌ Error collecting metrics: {e}")
        db.rollback()
        return None