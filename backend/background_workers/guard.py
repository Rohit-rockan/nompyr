import os
import re
from shared.discord_notifier import guard_alert
from shared.logger import logger


# In a real environment, this would be the path to Nginx/Apache/Flask access logs
LOG_FILE_PATH = "nompyr.log" 

def scan_error_logs():
    """
    The Guard's patrol duty: scans application logs for suspicious activity
    like repeated 403s, 500s, or rate limit hits.
    """
    logger.info("Guard is patrolling the server logs...")
    
    if not os.path.exists(LOG_FILE_PATH):
        logger.warning(f"Guard could not find log file at {LOG_FILE_PATH}. Skipping patrol.")
        return

    try:
        # A simple scanner looking for error HTTP status codes or exceptions
        suspicious_entries = []
        
        # Read the last N lines (simplified for prototype)
        with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-100:] # Only check the last 100 entries to save memory
            
        for line in lines:
            # Look for 429 Too Many Requests, 500 Internal Error, or 403 Forbidden
            if re.search(r'\b(429|500|403)\b', line) or "Exception" in line or "Error" in line:
                suspicious_entries.append(line.strip())

        if len(suspicious_entries) > 5:
            # If there's a spike in errors or rate limits, sound the alarm
            message = (
                f"🚨 **SECURITY ALERT: Anomalous Traffic Detected**\n"
                f"The Guard has detected {len(suspicious_entries)} suspicious log entries in the recent patrol.\n"
                f"**Samples:**\n"
            )
            for entry in suspicious_entries[:3]:
                # Truncate long lines to prevent discord embed overflow
                message += f"```\n{entry[:100]}...\n```\n"
                
            message += "\n*Executing temporary rate-limit reinforcement...*"
            
            guard_alert(message)
            logger.info("Guard detected anomalies and dispatched a Discord alert.")
        else:
            logger.info("Guard patrol complete. Perimeter is secure.")
            
    except Exception as e:
        logger.error(f"Guard encountered a failure during log scanning: {e}")

def run_guard_tasks():
    """Wrapper function to be called by APScheduler in app.py"""
    scan_error_logs()
