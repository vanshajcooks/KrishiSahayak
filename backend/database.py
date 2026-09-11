"""
Smart Farming Assistant — SQLite Database Layer (SIH 26180)
Provides lightweight, local, offline-first telemetry persistence for Raspberry Pi / local deployment.
"""

import os
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union

from schemas import SensorReading

logger = logging.getLogger("smart_farming.database")

# Default production database location: backend/data/smart_farming.db
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "smart_farming.db"


def get_db_path() -> Path:
    """
    Resolves the active database path.
    Can be configured via the SQLITE_DB_PATH environment variable for testing/deployment.
    """
    env_path = os.environ.get("SQLITE_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


def _resolve_path(db_path: Optional[Union[str, Path]] = None) -> Path:
    """Helper to resolve and ensure explicit db_path takes precedence."""
    if db_path is not None:
        return Path(db_path)
    return get_db_path()


def get_connection(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """
    Creates and returns a SQLite connection with Row factory enabled.
    Ensures parent directories exist before connecting.
    """
    resolved_path = _resolve_path(db_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(resolved_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Union[str, Path]] = None) -> None:
    """
    Initializes the SQLite database schema if it does not exist.
    Safe to call multiple times; will never overwrite or destroy existing data.
    """
    resolved_path = _resolve_path(db_path)
    logger.info("Initializing SQLite database at: %s", resolved_path)

    with get_connection(resolved_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                soil_moisture REAL NOT NULL,
                rain_level REAL,
                battery_voltage REAL,
                timestamp TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp 
            ON sensor_telemetry (timestamp DESC);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_sensor_timestamp 
            ON sensor_telemetry (sensor_id, timestamp DESC);
        """)
        conn.commit()


def insert_reading(
    reading: SensorReading,
    db_path: Optional[Union[str, Path]] = None,
) -> int:
    """
    Inserts a validated SensorReading into the SQLite database.
    Timestamp is formatted and stored consistently in UTC ISO-8601.
    Returns the integer primary key id of the newly inserted row.
    """
    resolved_path = _resolve_path(db_path)

    # Normalize timestamp to UTC ISO-8601 string
    if reading.timestamp:
        if reading.timestamp.tzinfo is None:
            ts_str = reading.timestamp.replace(tzinfo=timezone.utc).isoformat()
        else:
            ts_str = reading.timestamp.astimezone(timezone.utc).isoformat()
    else:
        ts_str = datetime.now(timezone.utc).isoformat()

    conn = get_connection(resolved_path)
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sensor_telemetry (
                    sensor_id,
                    temperature,
                    humidity,
                    soil_moisture,
                    rain_level,
                    battery_voltage,
                    timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    reading.sensor_id,
                    reading.temperature,
                    reading.humidity,
                    reading.soil_moisture,
                    reading.rain_level,
                    reading.battery_voltage,
                    ts_str,
                ),
            )
            row_id = cursor.lastrowid
            if row_id is None:
                raise sqlite3.OperationalError("Failed to obtain lastrowid after telemetry insertion")
            return row_id
    finally:
        conn.close()


def get_latest_reading(
    sensor_id: Optional[str] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> Optional[dict]:
    """
    Retrieves the newest sensor reading from SQLite.
    Optionally filters by sensor_id.
    Uses 'timestamp DESC, id DESC' to ensure deterministic ordering.
    Returns a dict representation of the reading, or None if no records exist.
    """
    resolved_path = _resolve_path(db_path)
    conn = get_connection(resolved_path)
    try:
        cursor = conn.cursor()
        if sensor_id:
            cursor.execute(
                """
                SELECT id, sensor_id, temperature, humidity, soil_moisture,
                       rain_level, battery_voltage, timestamp
                FROM sensor_telemetry
                WHERE sensor_id = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT 1;
                """,
                (sensor_id,),
            )
        else:
            cursor.execute(
                """
                SELECT id, sensor_id, temperature, humidity, soil_moisture,
                       rain_level, battery_voltage, timestamp
                FROM sensor_telemetry
                ORDER BY timestamp DESC, id DESC
                LIMIT 1;
                """
            )
        row = cursor.fetchone()
        if not row:
            return None

        # Convert row to dictionary with datetime object
        data = dict(row)
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return data
    finally:
        conn.close()


def get_recent_readings(
    limit: int = 50,
    sensor_id: Optional[str] = None,
    db_path: Optional[Union[str, Path]] = None,
) -> List[dict]:
    """
    Retrieves up to 'limit' recent telemetry records in chronological order
    (oldest to newest) suitable for historical analysis and charts.
    """
    resolved_path = _resolve_path(db_path)
    conn = get_connection(resolved_path)
    try:
        cursor = conn.cursor()
        if sensor_id:
            cursor.execute(
                """
                SELECT id, sensor_id, temperature, humidity, soil_moisture,
                       rain_level, battery_voltage, timestamp
                FROM sensor_telemetry
                WHERE sensor_id = ?
                ORDER BY timestamp DESC, id DESC
                LIMIT ?;
                """,
                (sensor_id, limit),
            )
        else:
            cursor.execute(
                """
                SELECT id, sensor_id, temperature, humidity, soil_moisture,
                       rain_level, battery_voltage, timestamp
                FROM sensor_telemetry
                ORDER BY timestamp DESC, id DESC
                LIMIT ?;
                """,
                (limit,),
            )
        rows = cursor.fetchall()
        # rows are ordered newest -> oldest; reverse to chronological order (oldest -> newest)
        results = []
        for r in reversed(rows):
            d = dict(r)
            d["timestamp"] = datetime.fromisoformat(d["timestamp"])
            results.append(d)
        return results
    finally:
        conn.close()
