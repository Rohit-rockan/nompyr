import time
import schedule
from core.database import get_engagement_metrics, get_trending_anime
from shared.discord_notifier import send_discord_alert
from shared.logger import get_logger

logger = get_logger("MayorBot")

def generate_daily_report():
    """
    The Mayor's daily duty: generates an analytics report and sends it to Discord.
    """
    logger.info("Mayor is compiling the daily analytics report...")
    
    try:
        metrics = get_engagement_metrics()
        trending = get_trending_anime(limit=3)
        
        # Build the message
        message = (
            f"📈 **Daily Engagement Report**\n"
            f"**Total Streams:** {metrics.get('total_watches', 0)}\n"
            f"**Unique Active Citizens:** {metrics.get('unique_users', 0)}\n\n"
            f"🔥 **Top Trending Artifacts:**\n"
        )
        
        if not trending:
            message += "No trending data available today.\n"
        else:
            for idx, item in enumerate(trending, 1):
                message += f"{idx}. Anime ID: `{item['ani_id']}` ({item['watch_count']} streams)\n"
                
        message += "\n*Keep up the good work regulating the city.*"
        
        # Send via Discord Notifier using the MAYOR persona
        send_discord_alert(message, bot_type="MAYOR")
        logger.info("Mayor successfully broadcasted the daily report.")
        
    except Exception as e:
        logger.error(f"Mayor failed to generate report: {e}")

def run_mayor_tasks():
    """Wrapper function to be called by APScheduler in app.py"""
    generate_daily_report()
