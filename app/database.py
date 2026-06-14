import os
import re

# --- WINDOWS SYSTEM ENVIRONMENT SHIELD ---
# Programmatically clear any global Windows OS-level PGSSLMODE variables.
# This prevents asyncpg from reading corrupted global system variables and crashing.
os.environ.pop("PGSSLMODE", None)
# ----------------------------------------


from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

DATABASE_URL = settings.DATABASE_URL

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # --- SELF-HEALING POSTGRES/ASYNCPE CONNECTION REWRITER ---
    
    # 1. Force the asynchronous PostgreSQL driver scheme
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
        
# 2. Strip all query strings (such as ?sslmode=... or ?ssl=...)
    # This prevents SQLAlchemy from parsing them as strings and crashing asyncpg.
    if "?" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.split("?")[0]
        
    # 3. Pass the actual Python boolean 'True' to asyncpg via connect_args.
    # This completely bypasses asyncpg's string-based sslmode parser.
    connect_args["ssl"] = True


# Print configuration verification on boot (makes debugging easy)
print("\n--- DATABASE CONFIGURATION ACTIVE ---")
print(f"Connecting to: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
print("--------------------------------------\n")

engine = create_async_engine(DATABASE_URL, connect_args=connect_args, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
