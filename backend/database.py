"""
Smart Farming Assistant — SQLite Database Layer (SIH 26180)
Provides lightweight, local, offline-first telemetry persistence for Raspberry Pi / local deployment.
"""

import sys

if __name__ == "backend.database":
    sys.modules.setdefault("database", sys.modules[__name__])
elif __name__ == "database":
    sys.modules.setdefault("backend.database", sys.modules[__name__])
    try:
        import backend
        setattr(backend, "database", sys.modules[__name__])
    except ImportError:
        pass

import os
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union


try:
    from backend.schemas import SensorReading
except ImportError:
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
    Enables SQLite foreign keys for every connection.
    """
    resolved_path = _resolve_path(db_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(resolved_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[Union[str, Path]] = None) -> None:
    """
    Initializes the SQLite database schema and Phase 2 relational tables if they do not exist.
    Performs non-destructive schema upgrades (e.g. adds field_id to sensor_telemetry if missing).
    Safe to call multiple times; will never overwrite or destroy existing telemetry.
    """
    resolved_path = _resolve_path(db_path)
    logger.info("Initializing SQLite database at: %s", resolved_path)

    with get_connection(resolved_path) as conn:
        cursor = conn.cursor()

        # 1. Farmers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS farmers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                preferred_language TEXT NOT NULL DEFAULT 'en',
                state TEXT,
                district TEXT,
                village TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                last_login_at TEXT,
                token_version INTEGER NOT NULL DEFAULT 1,
                failed_login_count INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                deactivated_at TEXT
            );
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_farmers_phone ON farmers (phone);
        """)

        # Non-destructive check & addition of auth columns for existing databases
        cursor.execute("PRAGMA table_info(farmers);")
        farmer_cols = [row[1] for row in cursor.fetchall()]
        if "last_login_at" not in farmer_cols:
            cursor.execute("ALTER TABLE farmers ADD COLUMN last_login_at TEXT;")
        if "token_version" not in farmer_cols:
            cursor.execute("ALTER TABLE farmers ADD COLUMN token_version INTEGER NOT NULL DEFAULT 1;")
        if "failed_login_count" not in farmer_cols:
            cursor.execute("ALTER TABLE farmers ADD COLUMN failed_login_count INTEGER NOT NULL DEFAULT 0;")
        if "locked_until" not in farmer_cols:
            cursor.execute("ALTER TABLE farmers ADD COLUMN locked_until TEXT;")
        if "deactivated_at" not in farmer_cols:
            cursor.execute("ALTER TABLE farmers ADD COLUMN deactivated_at TEXT;")

        # 2. Fields table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE NOT NULL,
                farmer_id INTEGER NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                crop_type TEXT NOT NULL,
                sowing_date TEXT,
                soil_type TEXT,
                area_acres REAL,
                latitude REAL,
                longitude REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            );
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fields_farmer_id ON fields (farmer_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fields_uuid ON fields (uuid);
        """)

        # 3. Sensors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT UNIQUE NOT NULL,
                field_id INTEGER REFERENCES fields(id) ON DELETE SET NULL,
                hardware_type TEXT NOT NULL DEFAULT 'ESP32_DHT22_CAPACITIVE',
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                last_seen_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sensors_field_id ON sensors (field_id);
        """)

        # 4. Sensor telemetry table (preserves all existing columns, adds field_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id TEXT NOT NULL,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                soil_moisture REAL NOT NULL,
                rain_level REAL,
                battery_voltage REAL,
                timestamp TEXT NOT NULL,
                field_id INTEGER REFERENCES fields(id) ON DELETE SET NULL
            );
        """)

        # Non-destructive check & addition of field_id for existing databases
        cursor.execute("PRAGMA table_info(sensor_telemetry);")
        columns = [row[1] for row in cursor.fetchall()]
        if "field_id" not in columns:
            cursor.execute("ALTER TABLE sensor_telemetry ADD COLUMN field_id INTEGER REFERENCES fields(id) ON DELETE SET NULL;")

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp 
            ON sensor_telemetry (timestamp DESC);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_sensor_timestamp 
            ON sensor_telemetry (sensor_id, timestamp DESC);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_telemetry_field_timestamp 
            ON sensor_telemetry (field_id, timestamp DESC);
        """)

        # 5. Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE NOT NULL,
                farmer_id INTEGER NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
                field_id INTEGER REFERENCES fields(id) ON DELETE SET NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                action_recommended TEXT,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TEXT NOT NULL,
                acknowledged_at TEXT,
                resolved_at TEXT
            );
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_farmer_status_created 
            ON alerts (farmer_id, status, created_at DESC);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_field_status_created 
            ON alerts (field_id, status, created_at DESC);
        """)

        # 6. Notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
                farmer_id INTEGER NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
                channel TEXT NOT NULL,
                status TEXT NOT NULL,
                recipient TEXT,
                provider_message_id TEXT,
                error_message TEXT,
                sent_at TEXT,
                delivered_at TEXT,
                read_at TEXT
            );
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_alert_id 
            ON notifications (alert_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_notifications_farmer_status 
            ON notifications (farmer_id, status);
        """)

        conn.commit()


def insert_reading(
    reading: SensorReading,
    db_path: Optional[Union[str, Path]] = None,
) -> int:
    """
    Inserts a validated SensorReading into the SQLite database.
    Automatically resolves sensor_id -> field_id if registered in sensors table.
    Updates sensor's last_seen_at timestamp if sensor exists.
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

            # Resolve sensor_id -> field_id automatically
            cursor.execute("SELECT field_id FROM sensors WHERE sensor_id = ? LIMIT 1;", (reading.sensor_id,))
            sensor_row = cursor.fetchone()
            field_id = sensor_row["field_id"] if sensor_row and sensor_row["field_id"] is not None else None

            cursor.execute(
                """
                INSERT INTO sensor_telemetry (
                    sensor_id,
                    temperature,
                    humidity,
                    soil_moisture,
                    rain_level,
                    battery_voltage,
                    timestamp,
                    field_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    reading.sensor_id,
                    reading.temperature,
                    reading.humidity,
                    reading.soil_moisture,
                    reading.rain_level,
                    reading.battery_voltage,
                    ts_str,
                    field_id,
                ),
            )
            row_id = cursor.lastrowid
            if row_id is None:
                raise sqlite3.OperationalError("Failed to obtain lastrowid after telemetry insertion")

            # Update sensor last_seen_at if registered
            if sensor_row is not None:
                cursor.execute(
                    "UPDATE sensors SET last_seen_at = ?, updated_at = ? WHERE sensor_id = ?;",
                    (ts_str, ts_str, reading.sensor_id),
                )

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
                       rain_level, battery_voltage, timestamp, field_id
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
                       rain_level, battery_voltage, timestamp, field_id
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
                       rain_level, battery_voltage, timestamp, field_id
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
                       rain_level, battery_voltage, timestamp, field_id
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
