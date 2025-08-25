# config.py - Enhanced with Improved GPS Settings
import os
import pyodbc
import math
import pandas as pd
from datetime import datetime
from typing import Union

# ---------- Toggle (change as needed) ----------
USE_SQL = True  # True => use SQL Server, False => use local CSV files

# ---------- CSV paths ----------
EMPLOYEE_MASTER_CSV = "data/employee_master.csv"
EMPLOYEE_DATA_CSV = "data/employee_data.csv"
SALARY_LOG_CSV = "data/salary_log.csv"
BADGE_DIR = "badge"
FEEDBACK_LOG_CSV = "data/feedback_log.csv"
VERIFIED_ADMINS_CSV = "data/verified_admins.csv"
RESIGNATION_LOG_CSV = "data/resignation_log.csv"
FEEDBACK_RAW_CSV = "data/feedback_raw.csv"
FEEDBACK_REVIEWED_CSV = "data/feedback_reviewed.csv"

# --- Data Sync Logic ---
# This is the temporary file used when SQL is down
TEMP_CSV_PATH = "temp_offline_data.csv"

# ---------- SQL settings (change these or use environment variables) ----------
SQL_DRIVER = os.getenv("SQL_DRIVER", "ODBC Driver 17 for SQL Server")
SQL_SERVER = os.getenv("SQL_SERVER", r".\SQL2022_DEV")  # e.g. "localhost\\SQLEXPRESS" or "192.168.1.10"
SQL_DATABASE = os.getenv("SQL_DATABASE", "ValidexDB")
# Optional SQL auth (if not using Trusted Connection)
SQL_UID = os.getenv("SQL_UID", "")  # set to "" to use Trusted_Connection
SQL_PWD = os.getenv("SQL_PWD", "")

# ---------- Table names ----------
EMPLOYEE_MASTER_TABLE = "dbo.employee_master"
EMPLOYEE_DATA_TABLE = "dbo.employee_data"
SALARY_LOG_TABLE = "dbo.salary_log"
FEEDBACK_LOG_TABLE = "dbo.feedback_log"
VERIFIED_ADMIN_TABLE = "dbo.verified_admins"
RESIGNATION_LOG_TABLE = "dbo.resignation_log"
FEEDBACK_RAW_TABLE = "dbo.feedback_raw"
FEEDBACK_REVIEWED_TABLE = "dbo.feedback_reviewed"

# ===== ENHANCED GPS/Location Settings =====
# Office location coordinates (UPDATE THESE WITH YOUR ACTUAL COORDINATES)
OFFICE_LOCATIONS = [
    {
        "lat": 17.70588,  # Mumbai coordinates - REPLACE WITH YOUR MAIN OFFICE
        "lon": 73.98451,
        "name": "Main Office Mumbai",
        "radius": 100,  # Allowed radius in meters
        "address": "Main Office Building, Mumbai"
    },
    {
        "lat": 19.0760,  # Delhi coordinates - REPLACE WITH YOUR BRANCH OFFICE
        "lon": 72.8777,
        "name": "Branch Office Delhi",
        "radius": 150,
        "address": "Branch Office, Delhi"
    },
    {
        "lat": 21.1458,  # Nagpur coordinates - ADD MORE OFFICES AS NEEDED
        "lon": 79.0882,
        "name": "Regional Office Nagpur",
        "radius": 200,
        "address": "Regional Office, Nagpur"
    }
]

# GPS Detection Settings
GPS_SETTINGS = {
    "auto_detection": True,  # Enable automatic GPS detection
    "high_accuracy": True,  # Request high accuracy GPS
    "timeout_ms": 15000,  # GPS timeout in milliseconds (15 seconds)
    "max_age_ms": 60000,  # Maximum age of cached location (1 minute)
    "retry_attempts": 3,  # Number of retry attempts if GPS fails
    "min_accuracy_meters": 100,  # Minimum required accuracy in meters
    "detection_delay_ms": 1000,  # Delay before starting auto-detection
}

# Location Verification Settings
LOCATION_VERIFICATION = {
    "strict_mode": True,  # Strict location verification
    "allow_manual_override": False,  # Allow manual coordinate input (for testing only)
    "log_all_attempts": True,  # Log all location detection attempts
    "require_movement_check": False,  # Check if user moved significantly (anti-spoofing)
}

# Mobile app settings (Enhanced)
MOBILE_SETTINGS = {
    "camera_quality": "high",  # Camera quality for face recognition
    "location_accuracy": "high",  # GPS accuracy requirement
    "face_match_threshold": 30,  # Face recognition threshold percentage
    "location_update_interval": 30000,  # Location update interval in milliseconds
    "offline_mode": True,  # Allow offline attendance (sync later)
    "auto_location_detection": True,  # Enable automatic location detection
    "show_location_on_map": True,  # Show user location on map
    "battery_optimization": True,  # Optimize for mobile battery
}

# Security Settings
SECURITY_SETTINGS = {
    "require_face_recognition": True,  # Mandatory face recognition
    "require_gps_verification": True,  # Mandatory GPS verification
    "session_timeout_minutes": 60,  # Session timeout
    "max_daily_checkins": 1,  # Maximum check-ins per day
    "prevent_duplicate_sessions": True,  # Prevent multiple sessions for same user
    "audit_all_activities": True,  # Audit all attendance activities
}

# Working Hours Configuration
WORKING_HOURS = {
    "check_in_start": "08:00",  # Earliest check-in time
    "check_in_end": "10:00",  # Latest check-in time (after this = late)
    "late_mark_threshold": "09:15",  # Time after which late mark is applied
    "lunch_break_start": "13:00",  # Lunch break start
    "lunch_break_end": "14:00",  # Lunch break end
    "check_out_start": "17:00",  # Earliest check-out time
    "overtime_start": "18:45",  # Overtime calculation starts after this
    "max_daily_hours": 12,  # Maximum allowed hours per day
}

# Notification Settings
NOTIFICATIONS = {
    "send_check_in_confirmation": True,  # Send confirmation after check-in
    "send_check_out_reminder": True,  # Remind to check-out
    "notify_admin_on_issues": True,  # Notify admin on GPS/face recognition issues
    "daily_attendance_summary": True,  # Send daily summary
}


# ---------- Connection helpers ----------
def get_sql_connection():
    """
    Returns a pyodbc connection using either SQL auth (if SQL_UID/SQL_PWD set)
    or Windows Trusted Connection (default).
    """
    if SQL_UID and SQL_PWD:
        conn_str = (
            f"Driver={{{SQL_DRIVER}}};"
            f"Server={SQL_SERVER};"
            f"Database={SQL_DATABASE};"
            f"UID={SQL_UID};PWD={SQL_PWD};"
        )
    else:
        conn_str = (
            f"Driver={{{SQL_DRIVER}}};"
            f"Server={SQL_SERVER};"
            f"Database={SQL_DATABASE};"
            f"Trusted_Connection=yes;"
        )
    return pyodbc.connect(conn_str)


def safe_get_conn() -> Union[pyodbc.Connection, None]:
    """Return SQL connection if USE_SQL=True, else None."""
    if not USE_SQL:
        return None
    try:
        return get_sql_connection()
    except pyodbc.Error as ex:
        print(f"SQL connection failed: {ex}. Returning None.")
        return None


# ---------- Small helpers ----------
def table_exists(conn, table_name):
    """
    Check if a table exists. Accepts 'schema.table' or 'table'.
    """
    if "." in table_name:
        schema, tname = table_name.split(".", 1)
    else:
        schema, tname = "dbo", table_name
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA=? AND TABLE_NAME=?",
        (schema.strip("[]"), tname.strip("[]"))
    )
    return cursor.fetchone()[0] > 0


def safe_float(value, precision=12, scale=4):
    """
    Convert a value to float suitable for SQL DECIMAL(precision,scale).
    Returns None for invalid/missing values.
    """
    try:
        if value is None:
            return None
        # pandas NaN handling
        if isinstance(value, float) and math.isnan(value):
            return None
        # empty string -> None
        if isinstance(value, str) and value.strip() == "":
            return None
        val = float(value)
        val = round(val, scale)
        max_val = 10 ** (precision - scale) - 1
        if abs(val) > max_val:
            return None
        return val
    except (TypeError, ValueError):
        return None


def strip_microseconds(dt):
    """
    Remove microseconds from datetime-like objects (to be compatible with SQL DATETIME).
    Returns None for NaT/invalid.
    """
    if pd.isnull(dt):
        return None
    # pandas Timestamp
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    if isinstance(dt, datetime):
        return dt.replace(microsecond=0)
    return None


def safe_datetime_for_sql(dt):
    """
    Convert pandas / python datetimes to safe datetime for SQL.
    Returns None if out of SQL DATETIME range or invalid.
    """
    clean = strip_microseconds(dt)
    if clean is None:
        return None
    # SQL Server datetime range starts at 1753
    if clean.year < 1753:
        return None
    return clean


def safe_date_for_sql(dt):
    """
    Convert various date formats to safe date for SQL.
    Handles pandas Timestamp, datetime, date objects, and strings.
    """
    if pd.isnull(dt) or dt is None:
        return None

    try:
        # If it's already a date object, return it
        if isinstance(dt, datetime.date) and not isinstance(dt, datetime.datetime):
            return dt

        # If it's a datetime object, extract date
        if isinstance(dt, datetime.datetime):
            return dt.date()

        # If it's a pandas Timestamp, extract date
        if isinstance(dt, pd.Timestamp):
            return dt.date()

        # If it's a string, try to parse it
        if isinstance(dt, str):
            try:
                parsed = pd.to_datetime(dt)
                return parsed.date()
            except:
                return None

        # Try to convert to datetime first, then extract date
        converted = pd.to_datetime(dt)
        if pd.isnull(converted):
            return None
        return converted.date()

    except Exception as e:
        print(f"Error converting date: {dt}, Error: {e}")
        return None


# ===== ENHANCED GPS UTILITY FUNCTIONS =====
def validate_coordinates(lat, lon):
    """
    Validate GPS coordinates are within reasonable bounds
    """
    try:
        lat = float(lat)
        lon = float(lon)

        # Basic coordinate validation
        if not (-90 <= lat <= 90):
            return False, "Latitude must be between -90 and 90"
        if not (-180 <= lon <= 180):
            return False, "Longitude must be between -180 and 180"

        # Check if coordinates are not (0,0) - likely invalid
        if lat == 0.0 and lon == 0.0:
            return False, "Invalid coordinates (0,0)"

        return True, "Valid coordinates"

    except (TypeError, ValueError):
        return False, "Invalid coordinate format"


def calculate_distance_to_offices(user_lat, user_lon):
    """
    Calculate distance to all office locations and return the closest one
    """
    from geopy.distance import geodesic

    is_valid, message = validate_coordinates(user_lat, user_lon)
    if not is_valid:
        return None, None, message

    user_location = (user_lat, user_lon)
    closest_office = None
    min_distance = float('inf')

    distances = []

    for office in OFFICE_LOCATIONS:
        office_location = (office["lat"], office["lon"])
        try:
            distance = geodesic(user_location, office_location).meters
            distances.append({
                "office": office,
                "distance_meters": distance,
                "within_radius": distance <= office["radius"]
            })

            if distance < min_distance:
                min_distance = distance
                closest_office = office

        except Exception as e:
            print(f"Error calculating distance to {office['name']}: {e}")
            continue

    return closest_office, distances, "Calculation successful"


def log_location_attempt(employee_id, username, lat, lon, success, details=""):
    """
    Log all location detection attempts for security audit
    """
    if not LOCATION_VERIFICATION.get("log_all_attempts", True):
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if success else "FAILED"

    log_entry = f"[{timestamp}] LOCATION_{status} - Employee: {employee_id} - User: {username} - Coords: {lat},{lon} - {details}\n"

    try:
        with open("location_audit.log", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Failed to write location log: {e}")


# ---------- Data Sync Functions ----------
def _save_to_csv(data: pd.DataFrame, file_path: str):
    """
    A helper function to append data to a CSV file.
    If the file doesn't exist, it creates it with headers.
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        file_exists = os.path.exists(file_path) and os.path.getsize(file_path) > 0
        data.to_csv(file_path, mode='a', header=not file_exists, index=False, encoding='utf-8')
        print(f"Data successfully saved to {file_path}.")

    except Exception as e:
        print(f"Error saving to CSV {file_path}: {e}")


def sync_offline_data():
    """
    Reads data from the temporary CSV and syncs it to the SQL database.
    This function should be called on app startup when in SQL mode.
    """
    if not USE_SQL:
        print("Not in SQL mode. Skipping offline data sync.")
        return

    if not os.path.exists(TEMP_CSV_PATH) or os.stat(TEMP_CSV_PATH).st_size == 0:
        print("No offline data to sync.")
        return

    print("Offline data found. Attempting to sync with SQL...")
    conn = safe_get_conn()
    if conn:
        try:
            offline_data = pd.read_csv(TEMP_CSV_PATH)
            print(f"Found {len(offline_data)} records to sync.")

            # IMPORTANT: This assumes the data is for a single table.
            # You may need to adapt this if you have multiple temporary files.
            offline_data.to_sql(EMPLOYEE_DATA_TABLE, conn, if_exists='append', index=False)

            # Backup the temp file before deleting
            backup_path = f"{TEMP_CSV_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(TEMP_CSV_PATH, backup_path)
            print(f"Sync complete. Temporary CSV backed up to: {backup_path}")

        except Exception as e:
            print(f"Failed to sync offline data to SQL: {e}. Retrying on next run.")
        finally:
            if conn:
                conn.close()
    else:
        print("SQL is still down. Cannot sync data at this time.")


def save_data(data: pd.DataFrame, table_name: str):
    """
    Saves data based on the USE_SQL configuration.
    - If USE_SQL is True, it attempts to save to SQL with a CSV fallback.
    - If USE_SQL is False, it saves directly to the permanent CSV file.

    Args:
        data (pd.DataFrame): The DataFrame containing new data to save.
        table_name (str): The name of the SQL table or CSV file to save to.
    """
    if USE_SQL:
        conn = safe_get_conn()
        if conn:
            print(f"SQL connection successful. Writing data to {table_name}.")
            try:
                data.to_sql(table_name, conn, if_exists='append', index=False)
                print("Data successfully written to SQL.")
            except Exception as e:
                print(f"Error writing to SQL: {e}. Saving to temporary CSV.")
                _save_to_csv(data, TEMP_CSV_PATH)
            finally:
                if conn:
                    conn.close()
        else:
            print("SQL connection failed. Saving data to temporary CSV.")
            _save_to_csv(data, TEMP_CSV_PATH)
    else:
        print(f"CSV-only mode. Saving data directly to corresponding CSV file.")
        # Map table names to CSV files
        csv_mapping = {
            EMPLOYEE_MASTER_TABLE: EMPLOYEE_MASTER_CSV,
            EMPLOYEE_DATA_TABLE: EMPLOYEE_DATA_CSV,
            SALARY_LOG_TABLE: SALARY_LOG_CSV,
            FEEDBACK_LOG_TABLE: FEEDBACK_LOG_CSV,
            VERIFIED_ADMIN_TABLE: VERIFIED_ADMINS_CSV,
            RESIGNATION_LOG_TABLE: RESIGNATION_LOG_CSV,
            FEEDBACK_RAW_TABLE: FEEDBACK_RAW_CSV,
            FEEDBACK_REVIEWED_TABLE: FEEDBACK_REVIEWED_CSV,
        }

        csv_file = csv_mapping.get(table_name)
        if csv_file:
            _save_to_csv(data, csv_file)
        else:
            print(f"Warning: Unknown table name {table_name}. Saving to generic CSV.")
            _save_to_csv(data, f"data/{table_name.replace('dbo.', '')}.csv")


# ===== LOCATION SERVICE FUNCTIONS =====
def get_office_locations_json():
    """
    Return office locations as JSON string for JavaScript integration
    """
    import json
    return json.dumps(OFFICE_LOCATIONS)


def create_location_verification_report(employee_id, username, location_data):
    """
    Create a comprehensive location verification report
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "employee_id": employee_id,
        "username": username,
        "location_data": location_data,
        "verification_status": "pending"
    }

    if location_data:
        lat = location_data.get("latitude")
        lon = location_data.get("longitude")

        if lat and lon:
            closest_office, distances, message = calculate_distance_to_offices(lat, lon)

            report.update({
                "coordinates": {"latitude": lat, "longitude": lon},
                "closest_office": closest_office["name"] if closest_office else None,
                "distances_to_offices": distances,
                "calculation_message": message,
                "verification_status": "verified" if any(d["within_radius"] for d in distances) else "denied"
            })

            # Log the attempt
            success = report["verification_status"] == "verified"
            log_location_attempt(
                employee_id,
                username,
                lat,
                lon,
                success,
                f"Closest office: {report['closest_office']}"
            )

    return report


# ===== ENHANCED ERROR HANDLING =====
class AttendanceSystemError(Exception):
    """Base exception for attendance system errors"""
    pass


class LocationVerificationError(AttendanceSystemError):
    """Exception raised when location verification fails"""
    pass


class DatabaseConnectionError(AttendanceSystemError):
    """Exception raised when database connection fails"""
    pass


class FaceRecognitionError(AttendanceSystemError):
    """Exception raised when face recognition fails"""
    pass


# ===== SYSTEM HEALTH CHECK =====
def system_health_check():
    """
    Perform a comprehensive system health check
    """
    health_report = {
        "timestamp": datetime.now().isoformat(),
        "database": {"status": "unknown", "details": ""},
        "gps_services": {"status": "unknown", "details": ""},
        "file_system": {"status": "unknown", "details": ""},
        "configuration": {"status": "unknown", "details": ""}
    }

    # Check database connection
    try:
        if USE_SQL:
            conn = safe_get_conn()
            if conn:
                conn.close()
                health_report["database"] = {"status": "healthy", "details": "SQL connection successful"}
            else:
                health_report["database"] = {"status": "degraded",
                                             "details": "SQL connection failed, using CSV fallback"}
        else:
            health_report["database"] = {"status": "healthy", "details": "Using CSV mode"}
    except Exception as e:
        health_report["database"] = {"status": "unhealthy", "details": f"Database error: {str(e)}"}

    # Check file system access
    try:
        required_dirs = ["data", "badge"]
        for dir_name in required_dirs:
            os.makedirs(dir_name, exist_ok=True)
        health_report["file_system"] = {"status": "healthy", "details": "All directories accessible"}
    except Exception as e:
        health_report["file_system"] = {"status": "unhealthy", "details": f"File system error: {str(e)}"}

    # Check GPS configuration
    try:
        if len(OFFICE_LOCATIONS) > 0:
            for office in OFFICE_LOCATIONS:
                is_valid, message = validate_coordinates(office["lat"], office["lon"])
                if not is_valid:
                    raise ValueError(f"Invalid coordinates for {office['name']}: {message}")
            health_report["gps_services"] = {"status": "healthy",
                                             "details": f"{len(OFFICE_LOCATIONS)} office locations configured"}
        else:
            health_report["gps_services"] = {"status": "unhealthy", "details": "No office locations configured"}
    except Exception as e:
        health_report["gps_services"] = {"status": "unhealthy", "details": f"GPS configuration error: {str(e)}"}

    # Check configuration
    try:
        required_settings = [GPS_SETTINGS, MOBILE_SETTINGS, SECURITY_SETTINGS, WORKING_HOURS]
        all_configured = all(isinstance(setting, dict) and len(setting) > 0 for setting in required_settings)
        if all_configured:
            health_report["configuration"] = {"status": "healthy", "details": "All configuration sections present"}
        else:
            health_report["configuration"] = {"status": "degraded", "details": "Some configuration sections missing"}
    except Exception as e:
        health_report["configuration"] = {"status": "unhealthy", "details": f"Configuration error: {str(e)}"}

    # Overall system status
    statuses = [section["status"] for section in health_report.values() if
                isinstance(section, dict) and "status" in section]
    if all(status == "healthy" for status in statuses):
        health_report["overall_status"] = "healthy"
    elif any(status == "unhealthy" for status in statuses):
        health_report["overall_status"] = "unhealthy"
    else:
        health_report["overall_status"] = "degraded"

    return health_report


# ===== INITIALIZATION FUNCTION =====
def initialize_system():
    """
    Initialize the attendance system with all required components
    """
    print("🚀 Initializing Attendance System...")

    # Create required directories
    required_dirs = ["data", "badge", "logs"]
    for dir_name in required_dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✅ Directory created/verified: {dir_name}")

    # Sync offline data if in SQL mode
    if USE_SQL:
        sync_offline_data()

    # Perform health check
    health = system_health_check()
    print(f"🏥 System health check: {health['overall_status'].upper()}")

    # Validate GPS configuration
    print(f"📍 GPS: {len(OFFICE_LOCATIONS)} office locations configured")
    for office in OFFICE_LOCATIONS:
        is_valid, message = validate_coordinates(office["lat"], office["lon"])
        status = "✅" if is_valid else "❌"
        print(f"  {status} {office['name']}: {office['lat']}, {office['lon']} ({message})")

    # Display key settings
    print(f"⚙️ Settings:")
    print(f"  - SQL Mode: {'Enabled' if USE_SQL else 'Disabled (CSV mode)'}")
    print(f"  - Auto GPS Detection: {'Enabled' if GPS_SETTINGS.get('auto_detection', False) else 'Disabled'}")
    print(
        f"  - Face Recognition Required: {'Yes' if SECURITY_SETTINGS.get('require_face_recognition', False) else 'No'}")
    print(f"  - Location Verification: {'Strict' if LOCATION_VERIFICATION.get('strict_mode', False) else 'Normal'}")

    print("🎉 System initialization complete!")
    return health


# ===== DEVELOPMENT HELPERS =====
def create_sample_employee_data():
    """
    Create sample employee data for testing (development only)
    """
    if not os.path.exists("data"):
        os.makedirs("data")

    sample_employees = pd.DataFrame([
        {"employee_id": "EMP001", "employee_name": "John Doe", "fixed_salary": 50000, "department": "IT"},
        {"employee_id": "EMP002", "employee_name": "Jane Smith", "fixed_salary": 45000, "department": "HR"},
        {"employee_id": "EMP003", "employee_name": "Bob Johnson", "fixed_salary": 55000, "department": "Finance"},
    ])

    sample_employees.to_csv(EMPLOYEE_MASTER_CSV, index=False)
    print(f"✅ Sample employee data created: {EMPLOYEE_MASTER_CSV}")


def create_test_coordinates():
    """
    Return test coordinates for development (near your office locations)
    """
    if OFFICE_LOCATIONS:
        main_office = OFFICE_LOCATIONS[0]
        # Return coordinates slightly offset from main office (within radius)
        return {
            "latitude": main_office["lat"] + 0.0001,  # ~11 meters offset
            "longitude": main_office["lon"] + 0.0001,
            "source": "Test Coordinates",
            "manual": True
        }
    return None


# Run initialization when module is imported
if __name__ == "__main__":
    # If config.py is run directly, perform initialization and health check
    health_report = initialize_system()

    print("\n" + "=" * 50)
    print("SYSTEM HEALTH REPORT")
    print("=" * 50)

    for component, status in health_report.items():
        if isinstance(status, dict) and "status" in status:
            print(f"{component.replace('_', ' ').title()}: {status['status'].upper()}")
            if status["details"]:
                print(f"  Details: {status['details']}")

    print("=" * 50)

    # Create sample data if none exists (development mode)
    if not os.path.exists(EMPLOYEE_MASTER_CSV):
        print("\n⚠️  No employee master data found. Creating sample data for testing...")
        create_sample_employee_data()
        print("📝 Remember to replace sample data with real employee data!")
else:
    # When imported as module, just sync offline data
    if USE_SQL:
        sync_offline_data()