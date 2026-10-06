"""Shared credential loading for legacy psycopg scripts. Never contains a password."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / 'backend' / '.env', override=False)


def psycopg_dsn() -> str:
    value = os.environ.get('DATABASE_URL')
    if not value:
        raise RuntimeError('Set DATABASE_URL in the environment before using a database script.')
    return value.replace('postgresql+asyncpg://', 'postgresql://', 1)

