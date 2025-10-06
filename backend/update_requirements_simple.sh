#!/bin/bash

# Script alternativo para atualizar requirements.txt usando pip-tools
# Mais simples mas requer instalação do pip-tools

set -e

echo "🔄 Atualizador de Requirements - Versão Alternativa"
echo ""

# Verificar se pip-tools está instalado
if ! pip show pip-tools &> /dev/null; then
    echo "📦 pip-tools não encontrado. Instalando..."
    pip install pip-tools
fi

echo "🔍 Criando requirements.in a partir do requirements.txt atual..."

# Criar arquivo .in sem as versões fixas
sed 's/==.*//' requirements.txt > requirements.in

echo "⬆️  Buscando versões mais recentes..."

# Compilar com as versões mais recentes
pip-compile --upgrade --resolver=backtracking requirements.in -o requirements.txt

echo ""
echo "✅ requirements.txt atualizado!"
echo ""
echo "📋 Diferenças:"
git diff requirements.txt || diff requirements.in requirements.txt || echo "Sem git/diff disponível"

echo ""
echo "🧹 Limpando arquivo temporário..."
rm requirements.in

echo ""
echo "✅ Concluído! Execute 'pip install -r requirements.txt --upgrade' para atualizar os pacotes"
