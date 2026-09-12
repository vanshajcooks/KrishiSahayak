"""
Development Provisioning Script — KhetSaathi (Phase 2)
Provision Demo Farmer -> Field 01 -> esp32_field_01 idempotently.
"""

import os
import sys
import uuid
import sqlite3
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union, Dict, Any

try:
    from backend.database import get_connection, init_db, get_db_path
except ImportError:
    from database import get_connection, init_db, get_db_path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("khetsaathi.dev_provision")


def provision_development_node(
    phone: str,
    db_path: Optional[Union[str, Path]] = None,
    farmer_name: str = "Demo Farmer",
    field_name: str = "Field 01",
    crop_type: str = "Tomato",
    soil_type: str = "Loam",
    area_acres: float = 1.0,
    sensor_id: str = "esp32_field_01",
    hardware_type: str = "ESP32_DHT22_CAPACITIVE",
) -> Dict[str, Any]:
    """
    Provisions a development farmer, field, and sensor node idempotently.
    """
    cleaned_phone = phone.strip()
    if not cleaned_phone:
        raise ValueError("DEV_FARMER_PHONE cannot be empty.")

    # Ensure tables and schema exist
    init_db(db_path)

    conn = get_connection(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        with conn:
            cursor = conn.cursor()

            # 1. Farmer lookup / insert
            cursor.execute("SELECT id, uuid, name, phone FROM farmers WHERE phone = ? LIMIT 1;", (cleaned_phone,))
            farmer_row = cursor.fetchone()
            if farmer_row:
                farmer_id = farmer_row["id"]
                farmer_uuid = farmer_row["uuid"]
                farmer_created = False
                logger.info(f"Existing farmer found: ID={farmer_id}, UUID={farmer_uuid}")
            else:
                farmer_uuid = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO farmers (uuid, name, phone, preferred_language, state, district, village, created_at, updated_at, is_active)
                    VALUES (?, ?, ?, 'en', 'Development', 'Local Testbed', 'Demo Village', ?, ?, 1);
                    """,
                    (farmer_uuid, farmer_name, cleaned_phone, now_iso, now_iso),
                )
                farmer_id = cursor.lastrowid
                farmer_created = True
                logger.info(f"Created new farmer: ID={farmer_id}, UUID={farmer_uuid}")

            # 2. Field lookup / insert
            cursor.execute(
                "SELECT id, uuid, name, crop_type FROM fields WHERE farmer_id = ? AND name = ? LIMIT 1;",
                (farmer_id, field_name),
            )
            field_row = cursor.fetchone()
            if field_row:
                field_id = field_row["id"]
                field_uuid = field_row["uuid"]
                field_created = False
                logger.info(f"Existing field found: ID={field_id}, UUID={field_uuid}")
            else:
                field_uuid = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO fields (uuid, farmer_id, name, crop_type, soil_type, area_acres, created_at, updated_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1);
                    """,
                    (field_uuid, farmer_id, field_name, crop_type, soil_type, area_acres, now_iso, now_iso),
                )
                field_id = cursor.lastrowid
                field_created = True
                logger.info(f"Created new field: ID={field_id}, UUID={field_uuid}")

            # 3. Sensor lookup / insert / link
            cursor.execute(
                "SELECT id, sensor_id, field_id, status FROM sensors WHERE sensor_id = ? LIMIT 1;",
                (sensor_id,),
            )
            sensor_row = cursor.fetchone()
            if sensor_row:
                sensor_pk = sensor_row["id"]
                cursor.execute(
                    """
                    UPDATE sensors
                    SET field_id = ?, status = 'ACTIVE', hardware_type = ?, updated_at = ?
                    WHERE id = ?;
                    """,
                    (field_id, hardware_type, now_iso, sensor_pk),
                )
                sensor_created = False
                logger.info(f"Existing sensor linked/updated: ID={sensor_pk}, sensor_id={sensor_id} -> field_id={field_id}")
            else:
                cursor.execute(
                    """
                    INSERT INTO sensors (sensor_id, field_id, hardware_type, status, created_at, updated_at)
                    VALUES (?, ?, ?, 'ACTIVE', ?, ?);
                    """,
                    (sensor_id, field_id, hardware_type, now_iso, now_iso),
                )
                sensor_pk = cursor.lastrowid
                sensor_created = True
                logger.info(f"Created new sensor: ID={sensor_pk}, sensor_id={sensor_id} -> field_id={field_id}")

            return {
                "farmer_id": farmer_id,
                "farmer_uuid": farmer_uuid,
                "farmer_created": farmer_created,
                "farmer_phone": cleaned_phone,
                "field_id": field_id,
                "field_uuid": field_uuid,
                "field_created": field_created,
                "field_name": field_name,
                "sensor_pk": sensor_pk,
                "sensor_id": sensor_id,
                "sensor_created": sensor_created,
                "status": "ACTIVE",
            }
    finally:
        conn.close()


def main():
    phone = os.environ.get("DEV_FARMER_PHONE")
    if not phone or not phone.strip():
        print("\n[ERROR] Environment variable DEV_FARMER_PHONE is not configured or is empty.", file=sys.stderr)
        print("Please set DEV_FARMER_PHONE before running provisioning.", file=sys.stderr)
        print("Example (PowerShell):   $env:DEV_FARMER_PHONE = \"+919876543210\"", file=sys.stderr)
        print("Example (cmd.exe):      set DEV_FARMER_PHONE=+919876543210\n", file=sys.stderr)
        sys.exit(1)

    result = provision_development_node(phone=phone)

    farmer_status = "(Created)" if result["farmer_created"] else "(Existing)"
    field_status = "(Created)" if result["field_created"] else "(Existing)"
    sensor_status = "(Created)" if result["sensor_created"] else "(Existing)"

    print("\n" + "=" * 60)
    print("  KHETSAATHI DEVELOPMENT PROVISIONING SUMMARY")
    print("=" * 60)
    print("Farmer:")
    print(f"  ID:    {result['farmer_id']} {farmer_status}")
    print(f"  UUID:  {result['farmer_uuid']}")
    print(f"  Phone: {result['farmer_phone']}")
    print("Field:")
    print(f"  ID:    {result['field_id']} {field_status}")
    print(f"  UUID:  {result['field_uuid']}")
    print(f"  Name:  {result['field_name']}")
    print("Sensor:")
    print(f"  PK:    {result['sensor_pk']} {sensor_status}")
    print(f"  ID:    {result['sensor_id']}")
    print(f"  Link:  Linked to Field ID {result['field_id']} (Status: {result['status']})")
    print("=" * 60)
    print("Development node provisioning completed successfully!\n")


if __name__ == "__main__":
    main()
