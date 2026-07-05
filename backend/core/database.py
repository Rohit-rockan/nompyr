# ==============================================================================
# CORE — SQLite Database Connection Management
# ==============================================================================
# Purpose:
#     Manages the SQLite database lifecycle: initialization, thread-local
#     connection pooling, and safe teardown. Wraps raw sqlite3 operations
#     behind a clean context-manager interface.
#
# Need:
#     SQLite connections are NOT thread-safe by default. This module provides
#     thread-local connections so that Flask's multi-threaded request handling
#     does not corrupt the database or raise "ProgrammingError: SQLite objects
#     created in a thread can only be used in that same thread."
# ==============================================================================

import os
import sqlite3
import threading

from config import Config


# ------------------------------------------------------------------------------
# Thread-Local Connection Storage
# ------------------------------------------------------------------------------
_thread_local = threading.local()


def get_db():
    """
    Get a thread-local SQLite connection.

    Detailed Use:
        Returns the existing database connection for the current thread,
        or creates a new one if none exists yet. Connections are stored in
        thread-local storage to ensure each thread has its own isolated
        connection (required by SQLite's threading model).

    Need:
        Flask handles requests across multiple threads. Without thread-local
        connections, concurrent requests would share a single connection,
        causing "database is locked" errors or data corruption.

    Returns:
        sqlite3.Connection: A thread-local SQLite connection.
    """
    if not hasattr(_thread_local, "connection") or _thread_local.connection is None:
        _thread_local.connection = sqlite3.connect(Config.DB_PATH)
        _thread_local.connection.row_factory = sqlite3.Row
    return _thread_local.connection


def close_db():
    """
    Close the thread-local database connection.

    Detailed Use:
        Safely closes and removes the database connection for the current
        thread. Called during Flask app teardown to prevent connection leaks.

    Need:
        Prevents resource leaks when threads are recycled by the thread pool.
        Each thread's connection is cleaned up after its request completes.
    """
    conn = getattr(_thread_local, "connection", None)
    if conn is not None:
        conn.close()
        _thread_local.connection = None


def init_db():
    """
    Initialize the SQLite database schema.

    Detailed Use:
        Creates the `reviews` table if it does not already exist. This is
        called once during application startup (in the app factory) to
        ensure the database is ready for read/write operations.

    Need:
        Required to store persistent community interactions: user reviews,
        ratings, and comments on specific anime entries. The table is
        created idempotently so restarts don't drop existing data.
    """
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    
    # Reviews Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ani_id TEXT NOT NULL,
            username TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Stream Cache Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stream_cache (
            cache_key TEXT PRIMARY KEY,
            stream_data TEXT NOT NULL,
            expires_at REAL NOT NULL
        )
    ''')
    
    # Watch History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watch_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            ani_id TEXT NOT NULL,
            episode_id TEXT NOT NULL,
            timestamp_seconds INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id, ani_id)
        )
    ''')
    
    conn.commit()
    conn.close()


def get_db_stats():
    """
    Retrieve database statistics for the admin dashboard.

    Detailed Use:
        Queries the reviews table for total review count, unique anime
        count, and database file size. Returns a summary dict.

    Need:
        Powers the admin dashboard's database health panel, giving the
        owner a quick overview of community engagement metrics.

    Returns:
        dict: Database statistics including review_count, anime_count,
              and db_size_kb.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM reviews")
        review_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT ani_id) FROM reviews")
        anime_count = cursor.fetchone()[0]

        conn.close()

        db_size = 0
        if os.path.exists(Config.DB_PATH):
            db_size = os.path.getsize(Config.DB_PATH) // 1024  # KB

        return {
            "review_count": review_count,
            "anime_count": anime_count,
            "db_size_kb": db_size,
        }
    except Exception as e:
        return {"error": str(e)}

# ------------------------------------------------------------------------------
# The Mayor Analytics Helpers
# ------------------------------------------------------------------------------

def get_engagement_metrics():
    """Returns overall engagement metrics for The Mayor's daily report."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM watch_history")
        total_watches = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM watch_history")
        unique_users = cursor.fetchone()[0]
        
        conn.close()
        return {
            "total_watches": total_watches,
            "unique_users": unique_users
        }
    except Exception:
        return {"total_watches": 0, "unique_users": 0}

def get_trending_anime(limit=5):
    """Returns the most frequently watched anime recently for The Mayor."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ani_id, COUNT(*) as watch_count 
            FROM watch_history 
            GROUP BY ani_id 
            ORDER BY watch_count DESC 
            LIMIT ?
        ''', (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception:
        return []
