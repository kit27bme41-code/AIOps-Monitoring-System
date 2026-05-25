from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3

app = FastAPI()

class LogEntry(BaseModel):
    timestamp: str
    service: str
    endpoint: str
    method: str
    status_code: int
    latency_ms: int
    error_message: str | None = None

def setup_db():
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            service TEXT,
            endpoint TEXT,
            method TEXT,
            status_code INTEGER,
            latency_ms INTEGER,
            error_message TEXT
        )
    ''')
    conn.commit()
    conn.close()

setup_db()

# 1. The original endpoint (catches data from the generator)
@app.post("/logs")
async def receive_log(log: LogEntry):
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO api_logs (timestamp, service, endpoint, method, status_code, latency_ms, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (log.timestamp, log.service, log.endpoint, log.method, log.status_code, log.latency_ms, log.error_message))
    conn.commit()
    conn.close()
    return {"status": "success"}

# 2. NEW: Serve the HTML Dashboard
@app.get("/")
def serve_dashboard():
    return FileResponse("index.html")

# 3. NEW: API endpoint for the chart to fetch live data
@app.get("/api/logs")
def get_recent_logs():
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    # Grab the 15 most recent logs
    cursor.execute("SELECT timestamp, status_code, latency_ms FROM api_logs ORDER BY id DESC LIMIT 15")
    rows = cursor.fetchall()
    conn.close()
    
    # Reverse the order so the chart draws left-to-right (oldest to newest)
    rows.reverse()
    
    # Format the data neatly for JavaScript
    logs = [{"time": r[0].split("T")[1][:8], "status": r[1], "latency": r[2]} for r in rows]
    return logs

if __name__ == "__main__":
    import uvicorn
    print("Starting Receiver Server and Dashboard on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)