import os
import shutil
from config import Config
from shared.discord_notifier import send_discord_alert
from shared.logger import get_logger

logger = get_logger("ManagerBot")

def check_resources():
    """
    The Manager's duty: ensures infrastructure resources are healthy.
    Monitors disk space (critical for Render's persistent SQLite storage) 
    and simulates memory monitoring.
    """
    logger.info("Manager is calculating infrastructure capacity...")
    alerts = []

    # 1. Check Disk Space
    try:
        # Check the directory where the DB is stored
        db_dir = os.path.dirname(Config.DB_PATH)
        if not db_dir:
            db_dir = "."
            
        total, used, free = shutil.disk_usage(db_dir)
        free_mb = free // (1024 * 1024)
        total_mb = total // (1024 * 1024)
        free_percent = (free / total) * 100

        # If less than 10% free or less than 50MB free
        if free_percent < 10 or free_mb < 50:
            alerts.append(f"Disk Space Critical: Only {free_mb}MB free ({free_percent:.1f}%).")
        
    except Exception as e:
        logger.error(f"Manager failed to check disk space: {e}")

    # 2. Check Memory (Simulation without requiring psutil dependency)
    try:
        import sys
        # Rough heuristic of the current Python process size
        mem_bytes = sys.getallocatedblocks() * 16 # Roughly 16 bytes per block in typical CPython
        mem_mb = mem_bytes / (1024 * 1024)
        
        if mem_mb > 500: # Threshold of 500MB
            alerts.append(f"High Memory Usage: Python process is allocating ~{mem_mb:.1f}MB.")
            
    except Exception as e:
        pass # Ignore

    # Dispatch alerts if thresholds breached
    if alerts:
        logger.warning(f"Manager detected {len(alerts)} resource warnings.")
        message = (
            "⚙️ **INFRASTRUCTURE ALERT: Resource Threshold Breached**\n"
            "The Manager has detected that server resources are running low:\n\n"
        )
        for alert in alerts:
            message += f"- {alert}\n"
            
        message += "\n*Consider upgrading instance capacity or triggering an auto-scale event.*"
        send_discord_alert(message, bot_type="MANAGER")
    else:
        logger.info("Manager reports sufficient capacity. No scaling required.")

def run_manager_tasks():
    """Wrapper function to be called by APScheduler in app.py"""
    check_resources()
