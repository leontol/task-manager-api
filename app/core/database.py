import os
from contextlib import asynccontextmanager
import psycopg2
from psycopg2 import pool

class DatabaseManager:
    def __init__(self):
        self.pool = None
        self.use_db = True  # Принудительно включаем PostgreSQL
    
    async def connect(self):
        if not self.use_db:
            print("⚠️ In-memory mode")
            return None
        
        # Параметры подключения - жёстко заданы
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'admin',
            'password': 'admin123',
            'database': 'taskdb'
        }
        
        print(f"Connecting to {db_config['host']}:{db_config['port']}...")
        
        try:
            self.pool = pool.SimpleConnectionPool(
                1, 10,
                **db_config
            )
            # Проверяем подключение
            conn = self.pool.getconn()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            self.pool.putconn(conn)
            print("✅ PostgreSQL connected successfully!")
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            self.pool = None
        
        return self.pool
    
    async def disconnect(self):
        if self.pool:
            self.pool.closeall()
    
    @asynccontextmanager
    async def get_connection(self):
        if not self.pool:
            yield None
        else:
            conn = self.pool.getconn()
            try:
                yield conn
            finally:
                self.pool.putconn(conn)
    
    @asynccontextmanager
    async def transaction(self):
        if not self.pool:
            yield None
        else:
            conn = self.pool.getconn()
            try:
                with conn:
                    yield conn
            finally:
                self.pool.putconn(conn)

db_manager = DatabaseManager()