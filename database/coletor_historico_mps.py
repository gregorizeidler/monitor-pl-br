"""
Coletor Histórico de Medidas Provisórias da Câmara dos Deputados
Busca MPs dos últimos N anos e salva no banco SQLite
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
from src.coletores.coleta_medidas_provisorias import classify_mp_importance

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"Accept": "application/json"}


def fetch_mps_by_year(year, page=1, max_items=100):
    """Busca Medidas Provisórias de um ano específico."""
    url = f"{BASE_URL}/proposicoes"
    params = {
        'ano': year,
        'siglaTipo': 'MPV',  # Medida Provisória
        'ordem': 'ASC',
        'ordenarPor': 'dataApresentacao',
        'itens': max_items,
        'pagina': page
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get('dados', [])
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar MPs para o ano {year}, página {page}: {e}")
        return []


def fetch_mp_details(mp_id):
    """Busca detalhes completos de uma Medida Provisória."""
    url = f"{BASE_URL}/proposicoes/{mp_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        mp = data.get('dados', {})
        status = mp.get('statusProposicao', {})
        
        # Calcular dias restantes (MPs têm prazo de 120 dias)
        data_apresentacao_str = mp.get('dataApresentacao', '')
        dias_restantes = None
        prazo_vencido = False
        
        if data_apresentacao_str:
            try:
                data_apresentacao = datetime.fromisoformat(data_apresentacao_str.replace('Z', '+00:00'))
                prazo_final = data_apresentacao + timedelta(days=120)
                dias_restantes = (prazo_final - datetime.now(data_apresentacao.tzinfo)).days
                
                if dias_restantes < 0:
                    prazo_vencido = True
                    dias_restantes = 0
            except Exception as e:
                logger.debug(f"Erro ao calcular prazo da MP {mp_id}: {e}")
        
        # Classificar importância e categoria
        importancia, categoria = classify_mp_importance(mp.get('ementa', ''))
        
        # Calcular nível de urgência
        nivel_urgencia = 1
        if dias_restantes is not None and not prazo_vencido:
            if dias_restantes <= 10:
                nivel_urgencia = 5
            elif dias_restantes <= 30:
                nivel_urgencia = 4
            elif dias_restantes <= 60:
                nivel_urgencia = 3
            elif dias_restantes <= 90:
                nivel_urgencia = 2
        
        return {
            'id': mp['id'],
            'numero': f"{mp['siglaTipo']} {mp['numero']}/{mp['ano']}",
            'ementa': mp.get('ementa', ''),
            'data_apresentacao': mp.get('dataApresentacao', ''),
            'status': status.get('descricaoTramitacao', 'N/A'),
            'dias_restantes': dias_restantes,
            'prazo_vencido': prazo_vencido,
            'nivel_urgencia': nivel_urgencia,
            'importancia': importancia,
            'categoria': categoria
        }
    
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar detalhes da MP {mp_id}: {e}")
        return None


def save_mp_to_db(mp_data):
    """Salva ou atualiza uma Medida Provisória no banco de dados."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO medidas_provisorias (
                id, numero, ementa, data_apresentacao, status,
                dias_restantes, prazo_vencido, nivel_urgencia,
                importancia, categoria, data_ultima_coleta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            mp_data['id'],
            mp_data['numero'],
            mp_data['ementa'],
            mp_data['data_apresentacao'],
            mp_data['status'],
            mp_data['dias_restantes'],
            mp_data['prazo_vencido'],
            mp_data['nivel_urgencia'],
            mp_data['importancia'],
            mp_data['categoria']
        ))
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Erro ao salvar MP {mp_data['id']} no banco: {e}")
        return False
    finally:
        conn.close()


def coletar_mps_historico(anos_historico=5, teste_modo=False, max_mps_teste=50):
    """
    Coleta Medidas Provisórias históricas e salva no banco de dados.
    
    Args:
        anos_historico (int): Quantidade de anos para buscar dados.
        teste_modo (bool): Se True, coleta apenas um número limitado de MPs.
        max_mps_teste (int): Número máximo de MPs para coletar em modo teste.
    """
    logger.info(f"--- Iniciando coleta histórica de Medidas Provisórias ({anos_historico} anos) ---")
    
    start_year = datetime.now().year - anos_historico
    current_year = datetime.now().year
    
    total_mps_coletadas = 0
    
    for year in range(start_year, current_year + 1):
        logger.info(f"Coletando MPs para o ano {year}...")
        
        page = 1
        while True:
            mps = fetch_mps_by_year(year, page=page)
            
            if not mps:
                break
            
            if teste_modo and total_mps_coletadas >= max_mps_teste:
                logger.info(f"Modo teste: Limite de {max_mps_teste} MPs atingido para o ano {year}.")
                return
            
            for mp_summary in mps:
                if teste_modo and total_mps_coletadas >= max_mps_teste:
                    break
                
                details = fetch_mp_details(mp_summary['id'])
                if details:
                    if save_mp_to_db(details):
                        total_mps_coletadas += 1
                        logger.debug(f"  MP {details['numero']} salva. Total: {total_mps_coletadas}")
                    else:
                        logger.warning(f"  Falha ao salvar MP {details['numero']}")
                
                time.sleep(0.15)  # Delay para respeitar rate limit
            
            if teste_modo and total_mps_coletadas >= max_mps_teste:
                break
            
            page += 1
            time.sleep(0.5)
        
        logger.info(f"  {total_mps_coletadas} MPs coletadas até agora.")
    
    logger.info(f"--- Coleta histórica de MPs finalizada. Total: {total_mps_coletadas} MPs ---")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Coletar Medidas Provisórias históricas da Câmara')
    parser.add_argument('--anos', type=int, default=5, help='Número de anos para coletar (padrão: 5)')
    parser.add_argument('--teste', action='store_true', help='Modo teste: coleta apenas 50 MPs')
    parser.add_argument('--max-teste', type=int, default=50, help='Máximo de MPs em modo teste')
    
    args = parser.parse_args()
    
    if args.teste:
        logger.info("=== MODO TESTE ATIVADO ===")
        coletar_mps_historico(anos_historico=1, teste_modo=True, max_mps_teste=args.max_teste)
    else:
        logger.info("=== MODO COMPLETO ===")
        coletar_mps_historico(anos_historico=args.anos)

