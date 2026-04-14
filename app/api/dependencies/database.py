from app.core.database import db_manager

async def get_db_connection():
    async with db_manager.get_connection() as connection:
        yield connection

async def get_db_transaction():
    async with db_manager.transaction() as connection:
        yield connection