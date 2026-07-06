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
import psycopg2
import psycopg2.extras
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
        if Config.DATABASE_URL:
            _thread_local.connection = psycopg2.connect(Config.DATABASE_URL, cursor_factory=psycopg2.extras.DictCursor, connect_timeout=3)
        else:
            raise ValueError("DATABASE_URL is not set!")
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
    Initialize the PostgreSQL database schema.

    Detailed Use:
        Creates the tables if they do not already exist. This is
        called once during application startup (in the app factory) to
        ensure the database is ready for read/write operations.

    Need:
        Required to store persistent community interactions: user reviews,
        ratings, and comments on specific anime entries.
    """
    if not Config.DATABASE_URL:
        print("DATABASE_URL not set. Skipping DB init.")
        return
        
    try:
        conn = psycopg2.connect(Config.DATABASE_URL, connect_timeout=3)
        cursor = conn.cursor()
        
        # Reviews Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
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
                expires_at DOUBLE PRECISION NOT NULL
            )
        ''')
        
        # Watch History Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watch_history (
                id SERIAL PRIMARY KEY,
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
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        # We don't raise the exception here to prevent the app from crashing on startup
        # if the database is temporarily unreachable or the DATABASE_URL is invalid.




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
        conn = psycopg2.connect(Config.DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM reviews")
        review_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT ani_id) FROM reviews")
        anime_count = cursor.fetchone()[0]

        cursor.execute("SELECT pg_database_size(current_database())")
        db_size_bytes = cursor.fetchone()[0]
        db_size = db_size_bytes // 1024  # KB

        conn.close()

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
        conn = psycopg2.connect(Config.DATABASE_URL)
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
        conn = psycopg2.connect(Config.DATABASE_URL, cursor_factory=psycopg2.extras.DictCursor)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ani_id, COUNT(*) as watch_count 
            FROM watch_history 
            GROUP BY ani_id 
            ORDER BY watch_count DESC 
            LIMIT %s
        ''', (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    except Exception:
        return []
