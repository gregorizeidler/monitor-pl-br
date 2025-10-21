"""
Coletor Histórico de Votações da Câmara dos Deputados
Busca votações dos últimos N anos e salva no banco SQLite
"""

import sqlite3
import requests
import logging
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.init_db import get_connection, DATABASE_FILE
from src.coletores.coleta_votacoes import classify_vote_importance

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"Accept": "application/json"}


def fetch_votes_by_period(start_date, end_date, page=1, max_items=100):
    """Busca votações em um período específico."""
    url = f"{BASE_URL}/votacoes"
    params = {
        'dataInicio': start_date.strftime('%Y-%m-%d'),
        'dataFim': end_date.strftime('%Y-%m-%d'),
        'ordem': 'ASC',
        'ordenarPor': 'dataHoraRegistro',
        'itens': max_items,
        'pagina': page
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get('dados', [])
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar votações para período {start_date} - {end_date}, página {page}: {e}")
        return []


def fetch_vote_details(vote_id):
    """Busca detalhes completos de uma votação."""
    url = f"{BASE_URL}/votacoes/{vote_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        votacao = response.json().get('dados', {})
        
        # Buscar votos individuais para contar
        votos_sim = 0
        votos_nao = 0
        votos_outros = 0
        votos_deputados = []
        
        try:
            url_votos = f"{BASE_URL}/votacoes/{vote_id}/votos"
            response_votos = requests.get(url_votos, headers=HEADERS, timeout=15)
            response_votos.raise_for_status()
            dados_votos = response_votos.json()
            
            for voto in dados_votos.get('dados', []):
                tipo_voto = voto.get('tipoVoto', '').lower()
                deputado_id = voto.get('deputado_', {}).get('id')
                
                if deputado_id:
                    votos_deputados.append({
                        'deputado_id': deputado_id,
                        'tipo_voto': tipo_voto
                    })
                
                if tipo_voto == 'sim':
                    votos_sim += 1
                elif tipo_voto == 'não' or tipo_voto == 'nao':
                    votos_nao += 1
                else:
                    votos_outros += 1
                    
        except Exception as e:
            logger.warning(f"Erro ao contar votos para votação {vote_id}: {e}")
        
        # Determinar aprovação
        aprovacao = None
        if votos_sim > votos_nao:
            aprovacao = True
        elif votos_nao > votos_sim:
            aprovacao = False
        
        return {
            'id': votacao.get('id', ''),
            'data': votacao.get('dataHoraRegistro', ''),
            'descricao': votacao.get('descricao', ''),
            'sigla_orgao': votacao.get('siglaOrgao', ''),
            'aprovacao': aprovacao,
            'votos_sim': votos_sim,
            'votos_nao': votos_nao,
            'votos_outros': votos_outros,
            'proposicao_id': votacao.get('proposicaoObjeto', {}).get('id', ''),
            'proposicao_numero': votacao.get('proposicaoObjeto', {}).get('descricao', ''),
            'votos_deputados': votos_deputados
        }
    
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar detalhes da votação {vote_id}: {e}")
        return None


def save_vote_to_db(vote_data):
    """Salva ou atualiza uma votação no banco de dados."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Classificar importância
        importancia = classify_vote_importance(vote_data)
        
        # Inserir votação
        cursor.execute("""
            INSERT OR REPLACE INTO votacoes (
                id, data_hora_registro, descricao, sigla_orgao,
                aprovacao, votos_sim, votos_nao, votos_outros,
                importancia, proposicao_id, proposicao_numero,
                data_ultima_coleta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            vote_data['id'],
            vote_data['data'],
            vote_data['descricao'],
            vote_data['sigla_orgao'],
            vote_data['aprovacao'],
            vote_data['votos_sim'],
            vote_data['votos_nao'],
            vote_data['votos_outros'],
            importancia,
            vote_data['proposicao_id'],
            vote_data['proposicao_numero']
        ))
        
        # Inserir votos individuais dos deputados
        for voto in vote_data.get('votos_deputados', []):
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO votos_deputados (
                        votacao_id, deputado_id, tipo_voto
                    ) VALUES (?, ?, ?)
                """, (
                    vote_data['id'],
                    voto['deputado_id'],
                    voto['tipo_voto']
                ))
            except sqlite3.Error as e:
                logger.debug(f"Erro ao inserir voto de deputado: {e}")
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Erro ao salvar votação {vote_data['id']} no banco: {e}")
        return False
    finally:
        conn.close()


def coletar_votacoes_historico(anos_historico=5, teste_modo=False, max_votes_teste=50):
    """
    Coleta votações históricas e salva no banco de dados.
    
    Args:
        anos_historico (int): Quantidade de anos para buscar dados.
        teste_modo (bool): Se True, coleta apenas um número limitado de votações.
        max_votes_teste (int): Número máximo de votações para coletar em modo teste.
    """
    logger.info(f"--- Iniciando coleta histórica de Votações ({anos_historico} anos) ---")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=anos_historico * 365)
    
    total_votes_coletadas = 0
    current_date = start_date
    
    # Coletar em chunks de 3 meses para evitar sobrecarga
    while current_date < end_date:
        chunk_end = min(current_date + timedelta(days=90), end_date)
        
        logger.info(f"Coletando votações de {current_date.strftime('%Y-%m-%d')} até {chunk_end.strftime('%Y-%m-%d')}...")
        
        page = 1
        while True:
            votes = fetch_votes_by_period(current_date, chunk_end, page=page)
            
            if not votes:
                break
            
            if teste_modo and total_votes_coletadas >= max_votes_teste:
                logger.info(f"Modo teste: Limite de {max_votes_teste} votações atingido.")
                return
            
            for vote_summary in votes:
                if teste_modo and total_votes_coletadas >= max_votes_teste:
                    break
                
                details = fetch_vote_details(vote_summary['id'])
                if details:
                    if save_vote_to_db(details):
                        total_votes_coletadas += 1
                        logger.debug(f"  Votação {details['id']} salva. Total: {total_votes_coletadas}")
                    else:
                        logger.warning(f"  Falha ao salvar votação {details['id']}")
                
                time.sleep(0.15)  # Delay para respeitar rate limit
            
            if teste_modo and total_votes_coletadas >= max_votes_teste:
                break
            
            page += 1
            time.sleep(0.5)
        
        logger.info(f"  {total_votes_coletadas} votações coletadas até agora.")
        current_date = chunk_end
    
    logger.info(f"--- Coleta histórica de Votações finalizada. Total: {total_votes_coletadas} votações ---")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Coletar votações históricas da Câmara')
    parser.add_argument('--anos', type=int, default=5, help='Número de anos para coletar (padrão: 5)')
    parser.add_argument('--teste', action='store_true', help='Modo teste: coleta apenas 50 votações')
    parser.add_argument('--max-teste', type=int, default=50, help='Máximo de votações em modo teste')
    
    args = parser.parse_args()
    
    if args.teste:
        logger.info("=== MODO TESTE ATIVADO ===")
        coletar_votacoes_historico(anos_historico=1, teste_modo=True, max_votes_teste=args.max_teste)
    else:
        logger.info("=== MODO COMPLETO ===")
        coletar_votacoes_historico(anos_historico=args.anos)

