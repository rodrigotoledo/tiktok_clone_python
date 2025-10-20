#!/usr/bin/env python3
import sys
import os
from sqlalchemy import create_engine, text, inspect

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATABASE_URL
from database import engine_pg

def safe_reset_database():
    """Reset seguro que lida com FKs"""
    print("🔒 Reset seguro do database...")

    inspector = inspect(engine_pg)
    tables = inspector.get_table_names()

    print(f"📋 Encontradas {len(tables)} tabelas: {tables}")

    with engine_pg.connect() as conn:
        # Método 1: Desabilita todas as constraints
        print("🔓 Desabilitando constraints...")
        conn.execute(text("SET session_replication_role = 'replica';"))

        # Drop todas as tabelas
        for table in tables:
            try:
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE;'))
                print(f"   ✅ {table}")
            except Exception as e:
                print(f"   ❌ {table}: {e}")

        # Re-habilita constraints
        conn.execute(text("SET session_replication_role = 'origin';"))
        conn.commit()

    print("🔄 Recriando tabelas...")
    from database import create_tables
    create_tables()

    print("🎉 Reset seguro completado!")

if __name__ == "__main__":
    confirm = input("❓ Reset seguro do database? (digite 'SEGURO'): ")

    if confirm.strip().upper() == "SEGURO":
        safe_reset_database()
    else:
        print("❌ Cancelado")
