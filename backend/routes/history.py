from flask import Blueprint, jsonify, request
from core.database import get_db

history_bp = Blueprint("history", __name__)

@history_bp.route("/api/history", methods=["POST"])
def update_history():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No JSON provided"}), 400
        
    session_id = data.get("session_id")
    ani_id = data.get("ani_id")
    episode_id = data.get("episode_id")
    timestamp = data.get("timestamp_seconds", 0)
    
    if not session_id or not ani_id or not episode_id:
        return jsonify({"success": False, "error": "Missing required fields"}), 400
        
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # INSERT OR REPLACE requires a UNIQUE constraint, which we have on (session_id, ani_id)
        cursor.execute('''
            INSERT INTO watch_history (session_id, ani_id, episode_id, timestamp_seconds, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id, ani_id) DO UPDATE SET
                episode_id = excluded.episode_id,
                timestamp_seconds = excluded.timestamp_seconds,
                updated_at = CURRENT_TIMESTAMP
        ''', (session_id, ani_id, episode_id, timestamp))
        
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@history_bp.route("/api/history", methods=["GET"])
def get_history():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"success": False, "error": "Missing session_id"}), 400
        
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ani_id, episode_id, timestamp_seconds, updated_at 
            FROM watch_history 
            WHERE session_id = ?
            ORDER BY updated_at DESC
            LIMIT 50
        ''', (session_id,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "ani_id": row["ani_id"],
                "episode_id": row["episode_id"],
                "timestamp_seconds": row["timestamp_seconds"],
                "updated_at": row["updated_at"]
            })
            
        return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
