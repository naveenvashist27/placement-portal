"""Create tables from SQLAlchemy metadata. Run: python -m scripts.init_db"""

import asyncio

from sqlalchemy import text

from app.core.database import Base, engine
from app import models  # noqa: F401


NEW_PROFILE_COLUMNS = [
    ("course", "VARCHAR(128)"),
    ("batch", "VARCHAR(32)"),
    ("cgpa", "DOUBLE PRECISION"),
    ("tenth_percentage", "DOUBLE PRECISION"),
    ("twelfth_percentage", "DOUBLE PRECISION"),
    ("has_atkt", "BOOLEAN"),
    ("atkt_count", "INTEGER"),
    ("current_semester", "INTEGER"),
    ("gender", "VARCHAR(32)"),
    ("date_of_birth", "DATE"),
    ("personal_email", "VARCHAR(255)"),
    ("city", "VARCHAR(128)"),
    ("linkedin_url", "VARCHAR(512)"),
    ("github_url", "VARCHAR(512)"),
]


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # create_all never alters existing tables, so add newer profile columns here.
        for column, sql_type in NEW_PROFILE_COLUMNS:
            await conn.execute(text(f"ALTER TABLE student_profiles ADD COLUMN IF NOT EXISTS {column} {sql_type}"))
        await conn.execute(text("ALTER TABLE registration_forms ADD COLUMN IF NOT EXISTS eligibility_json TEXT"))
    print("Database tables created.")


if __name__ == "__main__":
    asyncio.run(main())
