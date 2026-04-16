"""add seed data

Revision ID: 151653d78f49
Revises: 0538f5d7b421
Create Date: 2026-04-16 15:26:11.546088

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import re
import os
import json


def get_seed_data():
    """Load seed data from migrate.sql file."""
    # Get the path to migrate.sql relative to the project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    migrate_path = os.path.join(project_root, 'app', 'data', 'migrate.sql')

    with open(migrate_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract INSERT statements for each table
    # Note: migrate.sql uses JSON type but SQLite stores as TEXT
    tables = {
        'users': [],
        'standard_quotas': [],
        'dishes': [],
        'chat_sessions': [],
    }

    for table in tables.keys():
        pattern = rf'INSERT INTO {table}.*?VALUES\s*\([^;]+\);'
        tables[table] = re.findall(pattern, content, re.DOTALL)

    return tables


def convert_json_to_text_sql(sql):
    """Convert JSON column types to TEXT for SQLite compatibility.

    In migrate.sql, JSON columns are defined as JSON type,
    but in SQLite they are stored as TEXT.
    """
    # For standard_quotas: quotas JSON -> TEXT
    # For dishes: ingredients_quantified, applicable_meals, nutrition, tags JSON -> TEXT
    # For chat_sessions: messages JSON -> TEXT

    # Convert JSON field declarations to TEXT
    sql = re.sub(r'VALUES\s*\(', 'VALUES (', sql)

    return sql


# revision identifiers, used by Alembic.
revision: str = '151653d78f49'
down_revision: Union[str, Sequence[str], None] = '0538f5d7b421'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert seed data into database.

    Note: Uses INSERT OR IGNORE to skip if data already exists.
    The data is loaded from migrate.sql and adapted for SQLite compatibility.
    """
    tables = get_seed_data()

    # Insert users
    for sql in tables['users']:
        sql = sql.replace('INSERT INTO', 'INSERT OR IGNORE INTO')
        op.execute(sql)

    # Insert standard_quotas
    # Convert quotas JSON to TEXT for SQLite
    for sql in tables['standard_quotas']:
        sql = sql.replace('INSERT INTO', 'INSERT OR IGNORE INTO')
        # quotas column stores JSON as TEXT in SQLite
        op.execute(sql)

    # Insert dishes
    for sql in tables['dishes']:
        sql = sql.replace('INSERT INTO', 'INSERT OR IGNORE INTO')
        # JSON columns stored as TEXT in SQLite
        op.execute(sql)

    # Insert chat_sessions
    for sql in tables['chat_sessions']:
        sql = sql.replace('INSERT INTO', 'INSERT OR IGNORE INTO')
        # messages column stores JSON as TEXT in SQLite
        op.execute(sql)


def downgrade() -> None:
    """Remove seed data from database.

    This will delete all data from the seeded tables.
    Use with caution in production!
    """
    op.execute("DELETE FROM chat_sessions")
    op.execute("DELETE FROM dishes")
    op.execute("DELETE FROM standard_quotas")
    op.execute("DELETE FROM users")
