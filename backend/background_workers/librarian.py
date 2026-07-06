import time
from shared.logger import logger
from shared.discord_notifier import librarian_alert
from core.database import get_db_connection

def run_librarian_cleanup():
    """
    Background Task: Cleans up the database and orphaned records.
    Triggered via APScheduler.
    """
    logger.info("Librarian Bot starting scheduled database cleanup...")
    start_time = time.time()
    
    deleted_count = 0
    try:
        # Example Librarian task: 
        # Delete watch history entries that are older than a specific threshold
        # Or clean up orphaned reviews where the user might have been deleted
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            # Example: In a real scenario, you'd run something like:
            # cursor.execute("DELETE FROM watch_history WHERE updated_at < CURRENT_DATE - INTERVAL '365 days'")
            # deleted_count = cursor.rowcount
            # conn.commit()
            
            conn.close()
            
        elapsed = round(time.time() - start_time, 2)
        
        # Report success to Discord!
        librarian_alert(
            content=f"📚 **Librarian Cleanup Complete!**\n"
                    f"- **Task**: Database Maintenance\n"
                    f"- **Records Pruned**: {deleted_count}\n"
                    f"- **Time Taken**: {elapsed}s"
        )
        logger.info("Librarian cleanup finished successfully.")
        
    except Exception as e:
        logger.error(f"Librarian failed to execute cleanup: {str(e)}", exc_info=True)
        # We don't call mechanic_alert here because the global exception handler 
        # only catches Flask request errors, so we manually alert here if needed.
