"""
Coletor Histórico de Projetos de Lei
Busca PLs dos últimos 5 anos da API da Câmara e salva no banco
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"Accept": "application/json"}


def classificar_categoria(ementa):
    """Classifica categoria de um PL baseado na ementa"""
    ementa_lower = ementa.lower() if ementa else ''
    
    categorias = {
        'educação': ['educação', 'educacao', 'escola', 'professor', 'universidade', 'ensino'],
        'saúde': ['saúde', 'saude', 'sus', 'hospital', 'medicamento', 'médico', 'medico'],
        'economia': ['imposto', 'tributário', 'tributario', 'economia', 'financeiro', 'crédito', 'credito'],
        'segurança': ['segurança', 'seguranca', 'polícia', 'policia', 'crime', 'penal', 'prisão', 'prisao'],
        'trabalho': ['trabalho', 'trabalhador', 'emprego', 'salário', 'salario', 'clt'],
        'meio ambiente': ['meio ambiente', 'ambiental', 'clima', 'desmatamento', 'preservação', 'preservacao'],
        'direitos': ['direitos', 'mulher', 'criança', 'crianca', 'idoso', 'negro', 'lgbt', 'inclusão', 'inclusao']
    }
    
    for categoria, palavras in categorias.items():
        if any(palavra in ementa_lower for palavra in palavras):
            return categoria
    
    return 'diversos'


def classificar_importancia(pl):
    """Classifica importância de um PL (1-5)"""
    ementa = (pl.get('ementa') or '').lower()
    
    # Muito importante (5)
    if any(palavra in ementa for palavra in ['constituição', 'reforma', 'código', 'previdência']):
        return 5
    
    # Alta importância (4)
    if any(palavra in ementa for palavra in ['saúde', 'educação', 'segurança', 'trabalho']):
        return 4
    
    # Média importância (3)
    if any(palavra in ementa for palavra in ['imposto', 'tributo', 'servidor']):
        return 3
    
    return 2


def buscar_pls_por_ano(ano, limite=None):
    """Busca todos os PLs de um ano"""
    logger.info(f"🔍 Buscando PLs de {ano}...")
    
    try:
        url = f"{BASE_URL}/proposicoes"
        params = {
            'siglaTipo': 'PL',
            'ano': ano,
            'ordem': 'ASC',
            'ordenarPor': 'id',
            'itens': limite or 10000  # Máximo permitido
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        pls = data.get('dados', [])
        logger.info(f"✅ Encontrados {len(pls)} PLs em {ano}")
        
        return pls
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar PLs de {ano}: {e}")
        return []


def buscar_detalhes_pl(pl_id):
    """Busca detalhes completos de um PL"""
    try:
        url = f"{BASE_URL}/proposicoes/{pl_id}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        return data.get('dados', {})
        
    except Exception as e:
        logger.debug(f"Erro ao buscar detalhes do PL {pl_id}: {e}")
        return None


def salvar_pl(conn, pl):
    """Salva um PL no banco"""
    cursor = conn.cursor()
    
    try:
        # Classificar
        categoria = classificar_categoria(pl.get('ementa', ''))
        importancia = classificar_importancia(pl)
        
        cursor.execute("""
            INSERT OR REPLACE INTO projetos_lei 
            (id, numero, ano, ementa, autor_nome, tipo, data_apresentacao,
             status, categoria, importancia, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pl['id'],
            f"{pl.get('siglaTipo', 'PL')} {pl.get('numero', '')}/{pl.get('ano', '')}",
            pl.get('ano', 0),
            pl.get('ementa', ''),
            pl.get('nomeAutor', ''),
            pl.get('siglaTipo', 'PL'),
            pl.get('dataApresentacao', ''),
            pl.get('statusProposicao', {}).get('descricaoSituacao', ''),
            categoria,
            importancia,
            pl.get('uri', '')
        ))
        
        return True
        
    except Exception as e:
        logger.debug(f"Erro ao salvar PL {pl.get('id')}: {e}")
        return False


def registrar_coleta(conn, tipo, ano, mes, status, total_registros=0, erro=None):
    """Registra progresso da coleta"""
    cursor = conn.cursor()
    
    try:
        if status == 'in_progress':
            cursor.execute("""
                INSERT INTO coleta_historica (tipo, ano, mes, status, started_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (tipo, ano, mes, status))
        elif status == 'completed':
            cursor.execute("""
                UPDATE coleta_historica 
                SET status = ?, total_registros = ?, completed_at = CURRENT_TIMESTAMP
                WHERE tipo = ? AND ano = ? AND (mes IS NULL OR mes = ?) AND status = 'in_progress'
            """, (status, total_registros, tipo, ano, mes))
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Erro ao registrar coleta: {e}")


def coletar_pls_historicos(anos=5, limite_por_ano=None):
    """
    Coleta histórico de PLs dos últimos N anos
    
    Args:
        anos (int): Número de anos para buscar (padrão: 5)
        limite_por_ano (int): Limitar PLs por ano para teste (None = todos)
    """
    logger.info("╔═══════════════════════════════════════════════╗")
    logger.info("║  🗄️  COLETA HISTÓRICA DE PLs                ║")
    logger.info("╚═══════════════════════════════════════════════╝")
    logger.info("")
    logger.info(f"📅 Período: {anos} anos ({datetime.now().year - anos + 1} - {datetime.now().year})")
    if limite_por_ano:
        logger.info(f"⚠️  Modo teste: Limitado a {limite_por_ano} PLs por ano")
    logger.info("")
    
    # Conectar ao banco
    conn = get_connection()
    
    # Calcular período
    ano_atual = datetime.now().year
    ano_inicio = ano_atual - anos + 1
    
    total_pls = 0
    total_requisicoes = 0
    
    # Para cada ano
    for ano in range(ano_inicio, ano_atual + 1):
        logger.info(f"📊 Coletando PLs de {ano}...")
        
        # Registrar início
        registrar_coleta(conn, 'pls', ano, None, 'in_progress')
        
        # Buscar PLs do ano
        pls = buscar_pls_por_ano(ano, limite_por_ano)
        total_requisicoes += 1
        
        pls_salvos = 0
        
        # Salvar cada PL
        for i, pl in enumerate(pls, 1):
            if salvar_pl(conn, pl):
                pls_salvos += 1
                total_pls += 1
            
            # Commit a cada 100 PLs
            if i % 100 == 0:
                conn.commit()
                logger.info(f"   Progresso: {i}/{len(pls)} PLs ({pls_salvos} salvos)")
            
            # Rate limiting a cada 100 PLs
            if i % 100 == 0:
                time.sleep(1)
        
        # Commit final do ano
        conn.commit()
        registrar_coleta(conn, 'pls', ano, None, 'completed', pls_salvos)
        
        logger.info(f"   ✅ {ano}: {pls_salvos} PLs salvos")
    
    conn.close()
    
    logger.info("")
    logger.info("╔═══════════════════════════════════════════════╗")
    logger.info("║  ✅ COLETA CONCLUÍDA                         ║")
    logger.info("╚═══════════════════════════════════════════════╝")
    logger.info("")
    logger.info(f"📊 Estatísticas:")
    logger.info(f"   • Total de PLs coletados: {total_pls}")
    logger.info(f"   • Total de requisições: {total_requisicoes}")
    logger.info(f"   • Período: {ano_inicio}-{ano_atual}")
    logger.info("")
    logger.info(f"💾 Banco de dados: {DATABASE_FILE}")
    logger.info(f"📊 Tamanho: {Path(DATABASE_FILE).stat().st_size / 1024 / 1024:.2f} MB")
    logger.info("")


if __name__ == '__main__':
    import sys
    
    # Modo teste (100 PLs por ano)
    if len(sys.argv) > 1 and sys.argv[1] == '--teste':
        logger.info("🧪 Modo TESTE: Apenas 100 PLs por ano, últimos 2 anos")
        coletar_pls_historicos(anos=2, limite_por_ano=100)
    else:
        # Modo completo
        coletar_pls_historicos(anos=5)

