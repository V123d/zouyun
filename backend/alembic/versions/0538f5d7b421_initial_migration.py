"""initial migration

Revision ID: 0538f5d7b421
Revises:
Create Date: 2026-04-16 15:14:14.156246

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0538f5d7b421'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create all tables based on SQLAlchemy models.

    Tables are created with IF NOT EXISTS to handle existing databases.
    """
    # users table
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER NOT NULL PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            role VARCHAR(20) DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_username ON users (username)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_id ON users (id)")

    # chat_sessions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id VARCHAR(50) NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title VARCHAR(200) NOT NULL,
            messages TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id ON chat_sessions (user_id)")

    # dishes table
    op.execute("""
        CREATE TABLE IF NOT EXISTS dishes (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100) NOT NULL,
            ingredients_quantified TEXT NOT NULL,
            applicable_meals TEXT NOT NULL,
            flavor VARCHAR(100) NOT NULL,
            cost_per_serving FLOAT NOT NULL,
            nutrition TEXT NOT NULL,
            tags TEXT NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_dishes_id ON dishes (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_dishes_name ON dishes (name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_dishes_category ON dishes (category)")

    # menu_histories table
    op.execute("""
        CREATE TABLE IF NOT EXISTS menu_histories (
            id VARCHAR(50) NOT NULL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name VARCHAR(100),
            menu_data TEXT,
            metrics_data TEXT,
            config_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_menu_histories_user_id ON menu_histories (user_id)")

    # standard_quotas table
    op.execute("""
        CREATE TABLE IF NOT EXISTS standard_quotas (
            id INTEGER NOT NULL PRIMARY KEY,
            class_type VARCHAR(50) NOT NULL UNIQUE,
            quotas TEXT NOT NULL,
            is_system BOOLEAN DEFAULT 0,
            name VARCHAR(100),
            description VARCHAR(500),
            quota_type VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_standard_quotas_class_type ON standard_quotas (class_type)")


def downgrade() -> None:
    """Downgrade schema - drop all tables.

    Note: For production, this would typically be used only in development
    since dropping tables means losing all data.
    """
    op.execute("DROP TABLE IF EXISTS standard_quotas")
    op.execute("DROP TABLE IF EXISTS menu_histories")
    op.execute("DROP TABLE IF EXISTS dishes")
    op.execute("DROP TABLE IF EXISTS chat_sessions")
    op.execute("DROP TABLE IF EXISTS users")
