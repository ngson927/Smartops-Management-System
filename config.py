
import os

from dotenv import load_dotenv
from sqlalchemy.engine import URL


# ==========================================
# LOAD LOCAL ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()


# ==========================================
# DETECT RAILWAY ENVIRONMENT
# ==========================================

IS_RAILWAY = bool(
    os.getenv("RAILWAY_ENVIRONMENT_ID")
)


# ==========================================
# DATABASE CONFIGURATION
# ==========================================

def get_database_url():

    # --------------------------------------
    # RAILWAY MYSQL
    # --------------------------------------

    if IS_RAILWAY or os.getenv("MYSQLHOST"):

        required_variables = [
            "MYSQLHOST",
            "MYSQLPORT",
            "MYSQLUSER",
            "MYSQLPASSWORD",
            "MYSQLDATABASE"
        ]

        missing = [
            name
            for name in required_variables
            if not os.getenv(name)
        ]

        if missing:
            raise RuntimeError(
                "Missing Railway MySQL variables: "
                + ", ".join(missing)
            )

        return URL.create(
            drivername="mysql+pymysql",
            username=os.environ["MYSQLUSER"],
            password=os.environ["MYSQLPASSWORD"],
            host=os.environ["MYSQLHOST"],
            port=int(os.environ["MYSQLPORT"]),
            database=os.environ["MYSQLDATABASE"]
        )

    # --------------------------------------
    # LOCAL MYSQL
    # --------------------------------------

    local_password = os.getenv("DB_PASSWORD")

    if not local_password:
        raise RuntimeError(
            "DB_PASSWORD is missing from local environment."
        )

    return URL.create(
        drivername="mysql+pymysql",
        username=os.getenv(
            "DB_USER",
            "smartops_user"
        ),
        password=local_password,
        host=os.getenv(
            "DB_HOST",
            "127.0.0.1"
        ),
        port=int(
            os.getenv("DB_PORT", "3306")
        ),
        database=os.getenv(
            "DB_NAME",
            "smartops_db"
        )
    )


# ==========================================
# FLASK CONFIGURATION
# ==========================================

class Config:

    # --------------------------------------
    # APPLICATION SECURITY
    # --------------------------------------

    SECRET_KEY = os.getenv("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY environment variable is required."
        )

    # --------------------------------------
    # DATABASE
    # --------------------------------------

    SQLALCHEMY_DATABASE_URI = get_database_url()

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280
    }

    # --------------------------------------
    # SESSION SECURITY
    # --------------------------------------

    SESSION_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SAMESITE = "Lax"

    SESSION_COOKIE_SECURE = (
        IS_RAILWAY
        or os.getenv(
            "SESSION_COOKIE_SECURE",
            "false"
        ).lower() in {
            "true",
            "1",
            "yes"
        }
    )
