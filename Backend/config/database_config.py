import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'test@1234'),
    'database': os.getenv('DB_NAME', 'quartz_system'),
    'port': os.getenv('DB_PORT', 3306)
}

if not DATABASE_CONFIG['password']:
    print("WARNING: No database password set. Using in-memory storage.")
    USE_MEMORY_STORAGE = True
else:
    USE_MEMORY_STORAGE = False