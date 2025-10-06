#!/bin/bash

# Script para gerenciar o ambiente Docker do AI Agent Builder Pipeline

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções auxiliares
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Verificar se Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker não está instalado"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose não está instalado"
        exit 1
    fi
    
    print_success "Docker e Docker Compose encontrados"
}

# Criar arquivo .env se não existir
setup_env() {
    if [ ! -f ".env" ]; then
        print_info "Criando arquivo .env..."
        cp .env.docker.example .env
        print_success "Arquivo .env criado. Por favor, ajuste as configurações se necessário"
        print_warning "Editando .env em 5 segundos... (Ctrl+C para cancelar)"
        sleep 5
        ${EDITOR:-nano} .env
    else
        print_info "Arquivo .env já existe"
    fi
}

# Iniciar serviços
start() {
    print_info "Iniciando serviços..."
    docker-compose up -d
    print_success "Serviços iniciados"
    
    echo ""
    print_info "Aguardando serviços ficarem prontos..."
    sleep 5
    
    show_status
}

# Iniciar com ferramentas adicionais (pgAdmin, Redis)
start_with_tools() {
    print_info "Iniciando serviços com ferramentas adicionais..."
    docker-compose --profile tools up -d
    print_success "Serviços e ferramentas iniciados"
    
    echo ""
    print_info "Aguardando serviços ficarem prontos..."
    sleep 5
    
    show_status
}

# Parar serviços
stop() {
    print_info "Parando serviços..."
    docker-compose down
    print_success "Serviços parados"
}

# Parar e remover volumes
clean() {
    print_warning "Isso irá remover todos os dados (volumes). Continuar? (s/N)"
    read -r response
    if [[ "$response" =~ ^([sS][iI][mM]|[sS])$ ]]; then
        print_info "Parando serviços e removendo volumes..."
        docker-compose down -v
        print_success "Serviços parados e dados removidos"
    else
        print_info "Operação cancelada"
    fi
}

# Reiniciar serviços
restart() {
    print_info "Reiniciando serviços..."
    docker-compose restart
    print_success "Serviços reiniciados"
    show_status
}

# Mostrar logs
logs() {
    if [ -z "$1" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$1"
    fi
}

# Mostrar status dos serviços
show_status() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_info "Status dos Serviços:"
    docker-compose ps
    
    echo ""
    print_info "URLs de Acesso:"
    echo "  🚀 API Backend:    http://localhost:8000"
    echo "  📚 API Docs:       http://localhost:8000/docs"
    echo "  🗄️  PostgreSQL:     localhost:5432"
    
    # Verificar se pgAdmin está rodando
    if docker-compose ps | grep -q "ai-agent-pgadmin.*Up"; then
        echo "  🔧 pgAdmin:        http://localhost:5050"
    fi
    
    # Verificar se Redis está rodando
    if docker-compose ps | grep -q "ai-agent-redis.*Up"; then
        echo "  📦 Redis:          localhost:6379"
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Executar migrações
migrate() {
    print_info "Executando migrações do banco de dados..."
    docker-compose exec backend alembic upgrade head
    print_success "Migrações executadas"
}

# Criar nova migração
create_migration() {
    if [ -z "$1" ]; then
        print_error "Por favor, forneça uma descrição para a migração"
        echo "Uso: $0 migration 'descrição da migração'"
        exit 1
    fi
    
    print_info "Criando nova migração: $1"
    docker-compose exec backend alembic revision --autogenerate -m "$1"
    print_success "Migração criada"
}

# Acessar shell do backend
shell() {
    print_info "Acessando shell do backend..."
    docker-compose exec backend /bin/bash
}

# Acessar PostgreSQL
psql() {
    print_info "Acessando PostgreSQL..."
    docker-compose exec postgres psql -U user -d ai_agent_builder
}

# Backup do banco de dados
backup() {
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    print_info "Criando backup do banco de dados: $BACKUP_FILE"
    docker-compose exec -T postgres pg_dump -U user ai_agent_builder > "$BACKUP_FILE"
    print_success "Backup criado: $BACKUP_FILE"
}

# Restaurar banco de dados
restore() {
    if [ -z "$1" ]; then
        print_error "Por favor, forneça o arquivo de backup"
        echo "Uso: $0 restore backup_file.sql"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Arquivo não encontrado: $1"
        exit 1
    fi
    
    print_warning "Isso irá sobrescrever o banco de dados atual. Continuar? (s/N)"
    read -r response
    if [[ "$response" =~ ^([sS][iI][mM]|[sS])$ ]]; then
        print_info "Restaurando backup: $1"
        docker-compose exec -T postgres psql -U user ai_agent_builder < "$1"
        print_success "Backup restaurado"
    else
        print_info "Operação cancelada"
    fi
}

# Rebuild das imagens
rebuild() {
    print_info "Reconstruindo imagens Docker..."
    docker-compose build --no-cache
    print_success "Imagens reconstruídas"
}

# Mostrar ajuda
show_help() {
    cat << EOF

╔══════════════════════════════════════════════════════════════╗
║     🐳 Docker Manager - AI Agent Builder Pipeline          ║
╚══════════════════════════════════════════════════════════════╝

Uso: $0 [comando]

📋 COMANDOS DISPONÍVEIS:

  Gerenciamento de Serviços:
    start              Iniciar todos os serviços
    start-all          Iniciar com ferramentas extras (pgAdmin, Redis)
    stop               Parar todos os serviços
    restart            Reiniciar todos os serviços
    status             Mostrar status dos serviços
    clean              Parar e remover volumes (apaga dados!)

  Logs e Debugging:
    logs [service]     Mostrar logs (sem service = todos)
    shell              Acessar shell do backend
    psql               Acessar PostgreSQL CLI

  Banco de Dados:
    migrate            Executar migrações
    migration <msg>    Criar nova migração
    backup             Criar backup do banco
    restore <file>     Restaurar backup do banco

  Build:
    rebuild            Reconstruir imagens Docker

  Outros:
    setup              Configurar ambiente (.env)
    help               Mostrar esta ajuda

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 EXEMPLOS:

  # Primeiro uso
  $0 setup
  $0 start

  # Ver logs do backend
  $0 logs backend

  # Criar migração
  $0 migration "adicionar tabela de usuarios"

  # Backup do banco
  $0 backup

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
}

# Main
check_docker

case "${1:-help}" in
    start)
        setup_env
        start
        ;;
    start-all)
        setup_env
        start_with_tools
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    clean)
        clean
        ;;
    logs)
        logs "${2:-}"
        ;;
    status)
        show_status
        ;;
    migrate)
        migrate
        ;;
    migration)
        create_migration "${2:-}"
        ;;
    shell)
        shell
        ;;
    psql)
        psql
        ;;
    backup)
        backup
        ;;
    restore)
        restore "${2:-}"
        ;;
    rebuild)
        rebuild
        ;;
    setup)
        setup_env
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Comando desconhecido: $1"
        show_help
        exit 1
        ;;
esac
