# 1. Criar ambiente virtual
cd backend
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Edite o .env com suas configurações

# 4. Configurar PostgreSQL (se necessário)
sudo -u postgres psql
CREATE USER user WITH PASSWORD 'password';
CREATE DATABASE ai_agent_builder OWNER user;
\q

# 5. Executar migrations
alembic upgrade head

# 6. Iniciar servidor
python main.py
# ou
uvicorn main:app --reload