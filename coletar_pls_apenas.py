#!/usr/bin/env python3
"""
Script para coletar e rastrear Projetos de Lei SEM postar no X
Usado apenas para popular o dashboard com dados
"""

import sys
import os
import json
import logging
from datetime import datetime

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.dirname(__file__))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar módulos do projeto
from src.coletores.coleta_projetos_lei import (
    fetch_recent_projects,
    get_project_details,
    classify_project_importance
)

# Caminho do arquivo de estado
ESTADO_FILE = 'estado.json'


def carregar_estado():
    """Carrega o estado atual do bot"""
    if os.path.exists(ESTADO_FILE):
        with open(ESTADO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'last_processed_deputy_index': 0,
        'posted_news': [],
        'tracked_projects': []
    }


def salvar_estado(estado):
    """Salva o estado atual do bot"""
    with open(ESTADO_FILE, 'w', encoding='utf-8') as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)
    logger.info(f"Estado salvo: {len(estado.get('tracked_projects', []))} PLs rastreados")


def main():
    logger.info("--- Iniciando coleta de Projetos de Lei (Modo Dashboard) ---")
    
    # Carregar estado
    estado = carregar_estado()
    
    # Buscar projetos recentes
    logger.info("Buscando projetos de lei recentes...")
    projetos = fetch_recent_projects(days=7, max_projects=30)
    
    if not projetos:
        logger.info("Nenhum projeto encontrado.")
        return
    
    logger.info(f"Encontrados {len(projetos)} projetos.")
    
    # Enriquecer dados dos projetos (buscar detalhes completos)
    logger.info("Enriquecendo dados dos projetos...")
    projetos_completos = []
    
    for projeto in projetos[:10]:  # Processar os 10 mais recentes
        detalhes = get_project_details(projeto['id'])
        if detalhes:
            # Classificar importância
            importancia, categoria = classify_project_importance(detalhes)
            
            detalhes['importancia'] = importancia
            detalhes['categoria'] = categoria
            projetos_completos.append(detalhes)
    
    # Atualizar tracked_projects
    tracked_projects = estado.get('tracked_projects', [])
    tracked_ids = {p['id'] for p in tracked_projects}
    
    # Adicionar novos projetos
    novos_adicionados = 0
    for projeto in projetos_completos:
        if projeto['id'] not in tracked_ids and projeto['importancia'] >= 2:
            tracked_projects.append({
                'id': projeto['id'],
                'numero': projeto['numero'],
                'ementa': projeto['ementa'],  # Adicionar ementa (resumo)
                'categoria': projeto['categoria'],
                'importancia': projeto['importancia'],
                'last_status': projeto['status']['descricao_tramitacao'],
                'tracked_at': datetime.now().isoformat(),
                'posted': False
            })
            logger.info(f"  ✓ {projeto['numero']} - {projeto['categoria']} ({projeto['importancia']}⭐)")
            novos_adicionados += 1
    
    logger.info(f"{novos_adicionados} novos projetos adicionados")
    
    # Salvar estado atualizado
    estado['tracked_projects'] = tracked_projects
    salvar_estado(estado)
    
    logger.info("--- Coleta finalizada ---")
    logger.info(f"Total de PLs rastreados: {len(tracked_projects)}")
    
    # Mostrar resumo por categoria
    categorias = {}
    for p in tracked_projects:
        cat = p['categoria']
        categorias[cat] = categorias.get(cat, 0) + 1
    
    print("\n📊 Resumo por categoria:")
    for cat, count in sorted(categorias.items(), key=lambda x: x[1], reverse=True):
        print(f"   {cat}: {count}")
    
    print(f"\n✅ {len(tracked_projects)} PLs disponíveis no dashboard!")
    print("   Acesse: http://localhost:3001")


if __name__ == '__main__':
    main()

