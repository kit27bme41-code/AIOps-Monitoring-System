import json
import random
import time
import requests
from datetime import datetime, timezone

ENDPOINTS = ["/api/v1/auth", "/api/v1/users", "/api/v1/data-sync", "/api/v1/health"]
METHODS = ["GET", "POST", "PUT"]

def generate_log():
    # 85% chance of success, 10% chance of 400 error, 5% chance of 500 error
    scenario = random.random()
    
    if scenario < 0.85:
        status = random.choice([200, 201])
        latency = random.randint(20, 150)
        message = "Success"
    elif scenario < 0.95:
        status = random.choice([400, 401, 403, 404])
        latency = random.randint(30, 200)
        message = "Client Error - Invalid Request"
    else:
        status = random.choice([500, 502, 503])
        latency = random.randint(1000, 5000) # Simulating a major latency spike
        message = "Internal Server Error - Database Timeout"

    endpoint = random.choice(ENDPOINTS)
    
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "backend-api",
        "endpoint": endpoint,
        "method": random.choice(METHODS),
        "status_code": status,
        "latency_ms": latency,
        "error_message": message if status >= 400 else None
    }
    
    return log_entry

if __name__ == "__main__":
    print("Starting mock API log generation. Press Ctrl+C to stop.")
    try:
        while True:
            log = generate_log()
            
            # Print a short message to the console so we know it's working
            print(f"Sending log: {log['status_code']} - {log['endpoint']} (Latency: {log['latency_ms']}ms)")
            
            # Send the log to our FastAPI receiver
            try:
                # Timeout added so it doesn't hang forever if the receiver is down
                requests.post("https://ai-ops-dashboard-d8se.onrender.com/logs", json=log, timeout=2)
            except requests.exceptions.ConnectionError:
                print("Could not connect. Is the receiver.py server running?")
            except requests.exceptions.Timeout:
                print("Connection timed out. Receiver might be overloaded.")
            
            # Sleep between 0.1 to 2 seconds to simulate varied traffic
            time.sleep(random.uniform(0.1, 2.0))
    except KeyboardInterrupt:
        print("\nLog generation stopped.")