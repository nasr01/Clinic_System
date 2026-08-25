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


def create_tenant_database(database_name):
    """
    إنشاء PostgreSQL Database جديدة للـ Tenant.

    يتم استخدام اتصال PostgreSQL مستقل حتى لا يتأثر
    بـ transaction الخاصة بـ Django Admin.
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
                f'CREATE DATABASE "{database_name}"'
            )

    except psycopg.errors.DuplicateDatabase:
        raise ValueError(
            f'قاعدة البيانات "{database_name}" موجودة بالفعل.'
        )

    finally:
        if conn is not None:
            conn.close()