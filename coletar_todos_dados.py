#!/usr/bin/env python3
"""
Script para coletar TODOS os dados novos do Monitor PL Brasil
Executa: Votações, Medidas Provisórias e atualiza estado.json
"""

import sys
import os
import json
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.coletores.coleta_votacoes import (
    fetch_recent_votes,
    get_vote_details,
    classify_vote_importance
)
from src.coletores.coleta_medidas_provisorias import (
    fetch_active_mps,
    get_mp_details,
    calculate_mp_urgency,
    classify_mp_importance
)

ESTADO_FILE = 'estado.json'


def carregar_estado():
    """Carrega o estado atual"""
    if os.path.exists(ESTADO_FILE):
        with open(ESTADO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'last_processed_deputy_index': 0,
        'posted_news': [],
        'tracked_projects': [],
        'recent_votes': [],
        'active_mps': []
    }


def salvar_estado(estado):
    """Salva o estado atualizado"""
    with open(ESTADO_FILE, 'w', encoding='utf-8') as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)
    logger.info("Estado salvo com sucesso!")


def coletar_votacoes():
    """Coleta votações recentes"""
    logger.info("=== COLETANDO VOTAÇÕES ===")
    
    votacoes = fetch_recent_votes(days=7, max_votes=10)
    
    votacoes_completas = []
    for votacao in votacoes[:5]:  # Top 5 mais recentes
        detalhes = get_vote_details(votacao['id'])
        if detalhes:
            importancia = classify_vote_importance(detalhes)
            
            votacoes_completas.append({
                'id': detalhes['id'],
                'data': detalhes['data'],
                'descricao': detalhes['descricao'],
                'proposicao': detalhes['proposicao_numero'],
                'votos_sim': detalhes['votos_sim'],
                'votos_nao': detalhes['votos_nao'],
                'votos_outros': detalhes['votos_outros'],
                'aprovacao': detalhes['aprovacao'],
                'importancia': importancia,
                'coletado_em': datetime.now().isoformat()
            })
            logger.info(f"  ✓ {detalhes['proposicao_numero']} - {importancia}⭐")
    
    logger.info(f"Total de votações coletadas: {len(votacoes_completas)}")
    return votacoes_completas


def coletar_medidas_provisorias():
    """Coleta Medidas Provisórias ativas"""
    logger.info("=== COLETANDO MEDIDAS PROVISÓRIAS ===")
    
    mps = fetch_active_mps(max_mps=20)
    
    mps_completas = []
    for mp in mps[:10]:  # Top 10
        detalhes = get_mp_details(mp['id'])
        if detalhes:
            urgencia = calculate_mp_urgency(detalhes)
            importancia, categoria = classify_mp_importance(detalhes)
            
            # Só adicionar MPs com urgência >= 2 ou importância >= 3
            if urgencia['nivel_urgencia'] >= 2 or importancia >= 3:
                mps_completas.append({
                    'id': detalhes['id'],
                    'numero': detalhes['numero'],
                    'ementa': detalhes['ementa'],
                    'data_apresentacao': detalhes['data_apresentacao'],
                    'status': detalhes['status']['descricao'],
                    'dias_restantes': urgencia['dias_restantes'],
                    'nivel_urgencia': urgencia['nivel_urgencia'],
                    'prazo_vencido': urgencia['prazo_vencido'],
                    'importancia': importancia,
                    'categoria': categoria,
                    'coletado_em': datetime.now().isoformat()
                })
                
                urgencia_txt = f"⚠️ VENCIDA" if urgencia['prazo_vencido'] else f"{urgencia['dias_restantes']}d"
                logger.info(f"  ✓ {detalhes['numero']} - {urgencia_txt} - {importancia}⭐")
    
    logger.info(f"Total de MPs coletadas: {len(mps_completas)}")
    return mps_completas


def main():
    logger.info("╔═══════════════════════════════════════════════╗")
    logger.info("║  COLETOR COMPLETO - MONITOR PL BRASIL        ║")
    logger.info("╚═══════════════════════════════════════════════╝")
    logger.info("")
    
    # Carregar estado
    estado = carregar_estado()
    
    # Coletar votações
    votacoes = coletar_votacoes()
    estado['recent_votes'] = votacoes
    
    logger.info("")
    
    # Coletar MPs
    mps = coletar_medidas_provisorias()
    estado['active_mps'] = mps
    
    logger.info("")
    
    # Salvar estado
    salvar_estado(estado)
    
    # Resumo
    logger.info("╔═══════════════════════════════════════════════╗")
    logger.info("║  RESUMO DA COLETA                             ║")
    logger.info("╚═══════════════════════════════════════════════╝")
    logger.info(f"✅ Votações: {len(votacoes)}")
    logger.info(f"✅ Medidas Provisórias: {len(mps)}")
    logger.info(f"✅ Projetos de Lei: {len(estado.get('tracked_projects', []))}")
    logger.info(f"✅ Notícias: {len(estado.get('posted_news', []))}")
    logger.info("")
    logger.info("🌐 Dados disponíveis no dashboard!")
    logger.info("   http://localhost:3001")


if __name__ == '__main__':
    main()

