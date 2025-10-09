# 1. Aplicar migration
alembic upgrade head

# 2. Iniciar Redis
docker run -d -p 6379:6379 redis:alpine

# 3. Iniciar worker
./start_worker.sh

# 4. Iniciar API
python main.py

# 5. Testar
./test_r3_curl.sh
# Ou acessar: http://localhost:8000/docs