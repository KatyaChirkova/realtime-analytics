from __future__ import annotations

import argparse

from database import init_db


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Инициализация PostgreSQL")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    init_db(reset=args.reset)
    print("База данных инициализирована.")
