import os
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

print("=== .env file content ===")
print(f"USE_DATABASE: '{os.getenv('USE_DATABASE')}'")
print(f"API_KEY: '{os.getenv('API_KEY')}'")
print(f"DB_HOST: '{os.getenv('DB_HOST')}'")
print(f"DB_PORT: '{os.getenv('DB_PORT')}'")
print(f"DB_USER: '{os.getenv('DB_USER')}'")
print(f"DB_PASSWORD: '{os.getenv('DB_PASSWORD')}'")
print(f"DB_NAME: '{os.getenv('DB_NAME')}'")