import socket
import subprocess
import sys

def check_port(host, port):
    """Проверяет, открыт ли порт"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def check_docker():
    """Проверяет Docker"""
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

print("=== PostgreSQL Connection Diagnosis ===\n")

# 1. Проверяем Docker
print("1. Checking Docker...")
if check_docker():
    print("   ✅ Docker is running")
else:
    print("   ❌ Docker is NOT running")
    print("   → Start Docker Desktop first")

# 2. Проверяем порт
print("\n2. Checking port 5432...")
if check_port('localhost', 5432):
    print("   ✅ Port 5432 is open")
else:
    print("   ❌ Port 5432 is closed")
    print("   → PostgreSQL container is not running")

# 3. Проверяем контейнер
print("\n3. Checking container...")
result = subprocess.run(['docker', 'ps', '--filter', 'name=task_postgres', '--format', 'table {{.Names}}\t{{.Status}}'], 
                       capture_output=True, text=True)
if 'task_postgres' in result.stdout:
    print("   ✅ Container 'task_postgres' exists")
    print(f"   Status: {result.stdout.split()[1] if len(result.stdout.split()) > 1 else 'unknown'}")
else:
    print("   ❌ Container 'task_postgres' not found")
    print("   → Run: docker run -d --name task_postgres -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=admin123 -e POSTGRES_DB=taskdb -p 5432:5432 postgres:15")

print("\n=== Recommended actions ===")
print("1. Make sure Docker Desktop is running")
print("2. Run: docker start task_postgres")
print("3. Wait 10 seconds")
print("4. Run: docker exec -it task_postgres psql -U admin -d taskdb -c 'SELECT 1;'")