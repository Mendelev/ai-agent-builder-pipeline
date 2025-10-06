#!/usr/bin/env python3
"""
Script para atualizar automaticamente as versões das dependências no requirements.txt
com as versões mais recentes disponíveis no PyPI.
"""

import re
import subprocess
import sys
from typing import Dict, List, Tuple


def get_latest_version(package_name: str) -> str:
    """
    Obtém a versão mais recente de um pacote do PyPI usando pip index.
    
    Args:
        package_name: Nome do pacote (pode incluir extras como [standard])
    
    Returns:
        Versão mais recente do pacote
    """
    # Remove extras para buscar a versão
    base_package = package_name.split('[')[0].strip()
    
    try:
        # Usar pip index versions para obter a versão mais recente
        result = subprocess.run(
            ['pip', 'index', 'versions', base_package],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Procurar pela linha "Available versions:"
            for line in result.stdout.split('\n'):
                if 'Available versions:' in line:
                    # Pegar a primeira versão da lista (mais recente)
                    versions = line.split(':')[1].strip().split(',')
                    if versions and versions[0].strip():
                        return versions[0].strip()
        
        # Fallback: usar pip show (se o pacote estiver instalado)
        result = subprocess.run(
            ['pip', 'show', base_package],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    return line.split(':')[1].strip()
        
        print(f"⚠️  Não foi possível obter versão para {base_package}")
        return None
        
    except subprocess.TimeoutExpired:
        print(f"⏱️  Timeout ao buscar {base_package}")
        return None
    except Exception as e:
        print(f"❌ Erro ao buscar {base_package}: {e}")
        return None


def parse_requirements(file_path: str) -> List[Tuple[str, str, str]]:
    """
    Faz o parse do arquivo requirements.txt.
    
    Returns:
        Lista de tuplas (linha_original, nome_pacote, versao_atual)
    """
    requirements = []
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Ignorar linhas vazias e comentários
            if not line or line.startswith('#'):
                requirements.append((line, None, None))
                continue
            
            # Fazer parse da linha com versão
            match = re.match(r'^([a-zA-Z0-9\-_\[\]]+)==(.+)$', line)
            if match:
                package_name = match.group(1)
                current_version = match.group(2)
                requirements.append((line, package_name, current_version))
            else:
                # Linha sem versão específica
                requirements.append((line, None, None))
    
    return requirements


def update_requirements_file(file_path: str, dry_run: bool = False) -> None:
    """
    Atualiza o arquivo requirements.txt com as versões mais recentes.
    
    Args:
        file_path: Caminho para o arquivo requirements.txt
        dry_run: Se True, apenas mostra o que seria alterado sem modificar o arquivo
    """
    print("🔍 Analisando requirements.txt...\n")
    
    requirements = parse_requirements(file_path)
    updated_lines = []
    updates = []
    
    for original_line, package_name, current_version in requirements:
        # Manter comentários e linhas vazias
        if package_name is None:
            updated_lines.append(original_line)
            continue
        
        print(f"📦 Verificando {package_name}...", end=' ')
        
        latest_version = get_latest_version(package_name)
        
        if latest_version is None:
            print(f"⏭️  Mantendo versão atual")
            updated_lines.append(original_line)
            continue
        
        if latest_version != current_version:
            print(f"⬆️  {current_version} → {latest_version}")
            new_line = f"{package_name}=={latest_version}"
            updated_lines.append(new_line)
            updates.append((package_name, current_version, latest_version))
        else:
            print(f"✅ Já está atualizado ({current_version})")
            updated_lines.append(original_line)
    
    print("\n" + "="*60)
    
    if not updates:
        print("✅ Todas as dependências já estão atualizadas!")
        return
    
    print(f"\n📊 Resumo das atualizações ({len(updates)} pacotes):")
    for package, old, new in updates:
        print(f"  • {package}: {old} → {new}")
    
    if dry_run:
        print("\n🔍 Modo dry-run: Nenhuma alteração foi feita")
        print("\nConteúdo atualizado que seria gravado:")
        print("-" * 60)
        print('\n'.join(updated_lines))
        print("-" * 60)
        return
    
    # Escrever arquivo atualizado
    with open(file_path, 'w') as f:
        f.write('\n'.join(updated_lines) + '\n')
    
    print(f"\n✅ Arquivo {file_path} atualizado com sucesso!")
    print("\n💡 Recomendação: Execute 'pip install -r requirements.txt --upgrade' para atualizar os pacotes instalados")


def main():
    """Função principal do script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Atualiza requirements.txt com as versões mais recentes do PyPI'
    )
    parser.add_argument(
        '-f', '--file',
        default='requirements.txt',
        help='Caminho para o arquivo requirements.txt (padrão: requirements.txt)'
    )
    parser.add_argument(
        '-d', '--dry-run',
        action='store_true',
        help='Modo dry-run: mostra as mudanças sem modificar o arquivo'
    )
    
    args = parser.parse_args()
    
    try:
        update_requirements_file(args.file, dry_run=args.dry_run)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {args.file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
