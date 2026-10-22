"""Подключение к academy_db. Логин/пароль читаются из файла .env (он не попадает в git)."""
import os
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from sqlalchemy import create_engine, text


def _load_env(path=Path(__file__).with_name(".env")):
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


_load_env()

DSN = (
    f"postgresql://{quote_plus(os.environ['DB_USER'])}:{quote_plus(os.environ['DB_PASSWORD'])}"
    f"@{os.getenv('DB_HOST', 'thomas.proxy.rlwy.net')}:{os.getenv('DB_PORT', '51432')}"
    f"/{os.getenv('DB_NAME', 'academy_db')}"
)
engine = create_engine(DSN)


def q(sql: str) -> pd.DataFrame:
    """Выполнить SQL и вернуть DataFrame."""
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)
