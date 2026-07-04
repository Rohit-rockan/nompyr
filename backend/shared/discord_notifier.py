import os
import requests
from config import Config
from shared.logger import logger

# Bot Personas mapping to names and optional avatars
BOT_PERSONAS = {
    "Guard": {
        "username": "🛡️ The Guard",
        "avatar_url": "https://i.imgur.com/8Q5Z5T2.png" # Shield icon
    },
    "Mechanic": {
        "username": "🔧 The Mechanic",
        "avatar_url": "https://i.imgur.com/2X3ZQ9W.png" # Wrench icon
    },
    "Tester": {
        "username": "🧪 The Tester",
        "avatar_url": "https://i.imgur.com/Q9yZQ9W.png" # Beaker icon
    },
    "Manager": {
        "username": "⚙️ The Manager",
        "avatar_url": "https://i.imgur.com/4Y4ZQ9W.png" # Gear icon
    },
    "Librarian": {
        "username": "📚 The Librarian",
        "avatar_url": "https://i.imgur.com/5Z5ZQ9W.png" # Book icon
    },
    "Mayor": {
        "username": "🏛️ The Mayor",
        "avatar_url": "https://i.imgur.com/6A6ZQ9W.png" # Building icon
    }
}

def send_bot_message(bot_role: str, content: str, embeds: list = None):
    """
    Sends a message to the configured Discord Webhook URL acting as a specific bot.
    """
    webhook_url = getattr(Config, 'DISCORD_WEBHOOK_URL', None)
    
    if not webhook_url:
        logger.warning(f"DISCORD_WEBHOOK_URL not set. {bot_role} tried to say: {content}")
        return False
        
    persona = BOT_PERSONAS.get(bot_role, {"username": f"🤖 {bot_role}", "avatar_url": ""})
    
    payload = {
        "username": persona["username"],
        "avatar_url": persona["avatar_url"],
        "content": content
    }
    
    if embeds:
        payload["embeds"] = embeds
        
    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send Discord webhook message: {str(e)}")
        return False

# Convenience wrappers for specific bots
def guard_alert(content): send_bot_message("Guard", content)
def mechanic_alert(content, embeds=None): send_bot_message("Mechanic", content, embeds)
def tester_alert(content): send_bot_message("Tester", content)
def manager_alert(content): send_bot_message("Manager", content)
def librarian_alert(content): send_bot_message("Librarian", content)
def mayor_alert(content): send_bot_message("Mayor", content)
