import asyncio
import psycopg2

async def init_database():
    """Создание таблиц и индексов"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="admin",
            password="admin123",
            database="taskdb"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        print("✅ Connected to database!")
        
        # Создаём таблицу tasks
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id UUID PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                priority VARCHAR(10) NOT NULL DEFAULT 'medium',
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                completed_at TIMESTAMP
            )
        """)
        
        print("✅ Table 'tasks' created/verified")
        
        # Создаём индексы
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status 
            ON tasks(status)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_priority 
            ON tasks(priority)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status_priority 
            ON tasks(status, priority)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_created_at 
            ON tasks(created_at DESC)
        """)
        
        print("✅ All indexes created")
        
        # Проверяем
        cur.execute("SELECT COUNT(*) FROM tasks")
        count = cur.fetchone()[0]
        print(f"📊 Current tasks: {count}")
        
        cur.close()
        conn.close()
        print("\n✅ Database initialization completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Check:")
        print("   1. Run: docker ps")
        print("   2. Run: docker start task_postgres")
        print("   3. Run: docker logs task_postgres")

if __name__ == "__main__":
    asyncio.run(init_database())