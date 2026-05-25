import sqlite3
import os
import requests
from dotenv import load_dotenv
from google import genai

# 1. Load the secret keys from your .env file
load_dotenv()
api_key = os.getenv("API_KEY")
discord_url = os.getenv("DISCORD_WEBHOOK_URL")

if not api_key:
    print("Error: API_KEY not found. Please make sure you created a .env file with your key.")
    exit()

# 2. Set up the Gemini Client
client = genai.Client(api_key=api_key)

def fetch_recent_anomalies(limit=5):
    """Fetches the most recent API errors from the database."""
    conn = sqlite3.connect("logs.db")
    cursor = conn.cursor()
    
    query = """
        SELECT timestamp, endpoint, method, status_code, latency_ms, error_message
        FROM api_logs
        WHERE status_code >= 400
        ORDER BY id DESC
        LIMIT ?
    """
    
    try:
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()

def send_to_discord(report_text):
    """Pushes the AI report to a Discord channel via Webhook."""
    if not discord_url:
        print("⚠️ No Discord Webhook configured. Skipping chat alert.")
        return

    # Format the message for Discord
    payload = {
        "username": "AIOps Debugger Bot",
        "content": f"🚨 **API ANOMALY DETECTED** 🚨\n\n{report_text}"
    }
    
    try:
        response = requests.post(discord_url, json=payload)
        if response.status_code == 204:
            print("✅ Alert successfully pushed to Discord!")
        else:
            print(f"⚠️ Failed to send Discord alert. Status code: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Failed to connect to Discord: {e}")

def ask_ai_to_debug(anomalies):
    """Sends the logs to Gemini and asks for a debugging report."""
    
    log_text = ""
    for error in anomalies:
        timestamp, endpoint, method, status_code, latency, message = error
        log_text += f"- [{timestamp}] {method} {endpoint} | Status: {status_code} ({message}) | Latency: {latency}ms\n"

    prompt = f"""
    You are a Senior DevOps Engineer monitoring a backend API. 
    Our anomaly detection system just flagged the following recent API errors:
    
    {log_text}
    
    Please provide a concise debugging report with the following format:
    1. Incident Summary: (A one-sentence summary of what is going wrong)
    2. Root Cause Hypothesis: (What is the most likely cause based on the status codes and endpoints?)
    3. Actionable Steps: (3 exact steps developers should take right now to investigate or fix this)
    """

    print("🤖 Sending logs to Gemini for analysis...\n")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        print("================ AI DEBUGGING REPORT ================\n")
        print(response.text)
        print("\n=====================================================")
        
        # NEW: Push the final report to Discord!
        print("📡 Pushing alert to messaging channel...")
        send_to_discord(response.text)
        
    except Exception as e:
        print(f"Failed to connect to AI: {e}")

if __name__ == "__main__":
    print("--- API Anomaly Detector & AI Agent ---")
    print("Scanning database for recent errors...\n")
    
    anomalies = fetch_recent_anomalies(limit=5)
    
    if not anomalies:
        print("✅ System is healthy! No recent errors found.")
    else:
        print(f"🚨 FOUND {len(anomalies)} RECENT ANOMALIES. Triggering AI Agent...\n")
        ask_ai_to_debug(anomalies)