#!/bin/bash

# Quick Start: Atualizar Requirements
# Este script demonstra o uso básico do atualizador de dependências

echo "╔════════════════════════════════════════════════════════╗"
echo "║   🔄 Atualizador Automático de Dependências           ║"
echo "║   AI Agent Builder Pipeline                            ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Passo 1: Verificar o que seria atualizado
echo "📋 PASSO 1: Verificando atualizações disponíveis..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 update_requirements.py --dry-run

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "❓ Deseja aplicar essas atualizações? (s/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[SsYy]$ ]]; then
    # Passo 2: Criar backup
    echo ""
    echo "💾 PASSO 2: Criando backup..."
    cp requirements.txt requirements.txt.backup
    echo "✅ Backup criado: requirements.txt.backup"
    
    # Passo 3: Atualizar
    echo ""
    echo "⬆️  PASSO 3: Atualizando requirements.txt..."
    python3 update_requirements.py
    
    # Passo 4: Perguntar sobre instalação
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    read -p "❓ Deseja instalar as novas versões agora? (s/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[SsYy]$ ]]; then
        echo ""
        echo "📦 PASSO 4: Instalando pacotes atualizados..."
        pip install -r requirements.txt --upgrade
        
        echo ""
        echo "✅ Atualização concluída!"
        echo ""
        echo "🧪 Recomendação: Execute os testes para validar"
        echo "   pytest"
        echo ""
    else
        echo ""
        echo "⏭️  Instalação pulada. Para instalar depois execute:"
        echo "   pip install -r requirements.txt --upgrade"
        echo ""
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 Nota: Backup disponível em requirements.txt.backup"
    echo "   Para reverter: mv requirements.txt.backup requirements.txt"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo ""
    echo "❌ Atualização cancelada"
    echo ""
fi

echo ""
echo "📚 Para mais informações, consulte: DEPENDENCY_UPDATE_GUIDE.md"
echo ""
