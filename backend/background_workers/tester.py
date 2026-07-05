import requests
import sqlite3
from config import Config
from shared.discord_notifier import send_discord_alert
from shared.logger import get_logger

logger = get_logger("TesterBot")

def run_health_checks():
    """
    The Tester's duty: ensures the application and external APIs are healthy.
    """
    logger.info("Tester is running QA health checks...")
    failures = []

    # 1. Check local core API
    try:
        # Assuming we are running on localhost for the APScheduler
        resp = requests.get("http://127.0.0.1:5000/api/home", timeout=5)
        if resp.status_code != 200:
            failures.append(f"Local API `/api/home` returned {resp.status_code}")
    except requests.exceptions.RequestException as e:
        failures.append(f"Local API is unreachable: {e}")

    # 2. Check Database Integrity
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        if integrity != "ok":
            failures.append(f"SQLite integrity check failed: {integrity}")
        
        # Verify core tables exist
        cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='watch_history'")
        if cursor.fetchone()[0] != 1:
            failures.append("Missing critical table: `watch_history`")
            
        conn.close()
    except Exception as e:
        failures.append(f"Database check threw an exception: {e}")

    # Dispatch alerts if checks failed
    if failures:
        logger.error(f"Tester found {len(failures)} failures.")
        message = (
            "⚠️ **QA Health Check Failed!**\n"
            "The Tester has identified severe issues in the current environment:\n\n"
        )
        for fail in failures:
            message += f"- {fail}\n"
            
        message += "\n*Please investigate immediately.*"
        send_discord_alert(message, bot_type="TESTER")
    else:
        logger.info("Tester reports all systems are GO. Green light!")

def run_tester_tasks():
    """Wrapper function to be called by APScheduler in app.py"""
    run_health_checks()
