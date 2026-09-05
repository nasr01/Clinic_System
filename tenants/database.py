import re

import psycopg
from django.conf import settings


DATABASE_NAME_PATTERN = re.compile(
    r"^[a-zA-Z][a-zA-Z0-9_]{2,62}$"
)


def validate_database_name(database_name):
    """
    التأكد أن اسم قاعدة البيانات آمن ومسموح.
    """

    if not DATABASE_NAME_PATTERN.fullmatch(database_name):
        raise ValueError(
            "Invalid PostgreSQL database name."
        )


def database_exists(database_name):
    """
    Check if a PostgreSQL database exists.
    
    Returns True if the database exists, False otherwise.
    """
    validate_database_name(database_name)
    
    db_config = settings.DATABASES["default"]
    
    connection_params = {
        "host": db_config.get("HOST") or "127.0.0.1",
        "port": db_config.get("PORT") or 5432,
        "user": db_config.get("USER"),
        "password": db_config.get("PASSWORD"),
        "dbname": "postgres",
    }
    
    conn = None
    try:
        conn = psycopg.connect(
            **connection_params,
            autocommit=True,
        )
        
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (database_name,)
            )
            return cursor.fetchone() is not None
    
    finally:
        if conn is not None:
            conn.close()


def create_tenant_database(database_name):
    """
    إنشاء PostgreSQL Database جديدة للـ Tenant.

    يتم استخدام اتصال PostgreSQL مستقل حتى لا يتأثر
    بـ transaction الخاصة بـ Django Admin.
    
    Returns True if database was created by this operation.
    Returns False if database already existed (and raises error).
    """

    validate_database_name(database_name)
    
    # Check if database already exists BEFORE attempting creation
    if database_exists(database_name):
        raise ValueError(
            f'قاعدة البيانات "{database_name}" موجودة بالفعل. '
            f'لا يمكن إنشاء عيادة جديدة باسم موجود.'
        )

    db_config = settings.DATABASES["default"]

    connection_params = {
        "host": db_config.get("HOST") or "127.0.0.1",
        "port": db_config.get("PORT") or 5432,
        "user": db_config.get("USER"),
        "password": db_config.get("PASSWORD"),
        "dbname": "postgres",
    }

    conn = None

    try:
        conn = psycopg.connect(
            **connection_params,
            autocommit=True,
        )

        with conn.cursor() as cursor:
            cursor.execute(
                f'CREATE DATABASE "{database_name}"'
            )
        
        # Successfully created
        return True

    except psycopg.errors.DuplicateDatabase:
        # Race condition: database was created between check and creation
        raise ValueError(
            f'قاعدة البيانات "{database_name}" موجودة بالفعل.'
        )

    finally:
        if conn is not None:
            conn.close()


def drop_tenant_database(database_name):
    """
    Drop a PostgreSQL database.
    
    WARNING: This permanently destroys all data in the database.
    Only call this for cleanup of newly created databases during failed operations.
    """
    validate_database_name(database_name)
    
    db_config = settings.DATABASES["default"]
    
    connection_params = {
        "host": db_config.get("HOST") or "127.0.0.1",
        "port": db_config.get("PORT") or 5432,
        "user": db_config.get("USER"),
        "password": db_config.get("PASSWORD"),
        "dbname": "postgres",
    }
    
    conn = None
    try:
        conn = psycopg.connect(
            **connection_params,
            autocommit=True,
        )
        
        # Terminate existing connections to the database
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = %s
                  AND pid <> pg_backend_pid()
                """,
                (database_name,)
            )
        
        # Drop the database
        with conn.cursor() as cursor:
            cursor.execute(
                f'DROP DATABASE IF EXISTS "{database_name}"'
            )
    
    finally:
        if conn is not None:
            conn.close()