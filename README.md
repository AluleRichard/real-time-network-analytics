_credit to grok for assisting in formating this readme document_

# Real-Time Network Performance Analytics Dashboard

A professional real-time dashboard developed during my Bachelor's program to monitor and visualize network performance metrics.

## Features

- Real-time data collection every 30 seconds
- Live gauges for Download/Upload speed, Latency (Ping), and Packet Loss
- Interactive trend charts with Plotly
- WebSocket-based live updates
- Clean, modern dark-themed UI
- Persistent storage with SQLite

## Tech Stack

- **Backend**: FastAPI + WebSocket + SQLAlchemy
- **Frontend**: HTML + Plotly.js (single file)
- **Data Collection**: psutil, pythonping, Ookla Speedtest CLI
- **Database**: SQLite

## How to Run Locally

1. Clone the repository:
   ```bash
   git clone https://github.com/AluleRichard/real-time-network-analytics
   cd real-time-network-analytics
   ```
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependenciees:
   ```bash
   pip install fastapi uvicorn websockets sqlalchemy psutil pythonping
   ```
4. Install Ookla Speedtest CLI(Windows version)
5. Run the backend:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
6. Open dashboard.html in your browser

## Project Structure

network-dashboard/
├── app/
│ ├── **init**.py
│ ├── main.py
│ ├── database.py
│ ├── models.py
│ ├── schemas.py
│ └── collector.py
├── dashboard.html
├── .gitignore
└── README.md

## Screenshot

[To be added later]

Made with love as part of my Degree project
