from sqlmodel import create_engine
from app.config import settings

DB_URL = f"postgresql://{settings.db_user}:{settings.db_pass}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

engine = create_engine(DB_URL)