"""
Coletor Histórico de Gastos Parlamentares
Busca gastos dos últimos 5 anos da API da Câmara e salva no banco
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

# Configuração
ANOS_HISTORICO = 5
DATA_INICIO = datetime.now() - timedelta(days=365 * ANOS_HISTORICO)


def buscar_todos_deputados():
    """Busca lista completa de deputados"""
    logger.info("🔍 Buscando lista de deputados...")
    
    try:
        url = f"{BASE_URL}/deputados"
        params = {'itens': 600, 'ordem': 'ASC', 'ordenarPor': 'nome'}
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        deputados = data.get('dados', [])
        logger.info(f"✅ Encontrados {len(deputados)} deputados")
        
        return deputados
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar deputados: {e}")
        return []


def salvar_deputado(conn, deputado):
    """Salva ou atualiza informações de um deputado"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO deputados 
            (id, nome, partido, uf, email, legislatura_atual)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            deputado['id'],
            deputado['nome'],
            deputado.get('siglaPartido', ''),
            deputado.get('siglaUf', ''),
            deputado.get('email', ''),
            deputado.get('idLegislaturaUltimaEleicao', 0)
        ))
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Erro ao salvar deputado {deputado['id']}: {e}")
        return False


def buscar_gastos_deputado(deputado_id, ano, mes):
    """Busca gastos de um deputado em um ano/mês específico"""
    try:
        url = f"{BASE_URL}/deputados/{deputado_id}/despesas"
        params = {'ano': ano, 'mes': mes, 'itens': 100, 'ordem': 'ASC'}
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        return data.get('dados', [])
        
    except Exception as e:
        logger.debug(f"Erro ao buscar gastos do deputado {deputado_id} em {ano}/{mes}: {e}")
        return []


def salvar_gasto(conn, deputado_id, gasto):
    """Salva um gasto no banco"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO gastos 
            (deputado_id, ano, mes, tipo_despesa, valor_documento, valor_liquido,
             fornecedor, cnpj_fornecedor, numero_documento, data_documento, url_documento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            deputado_id,
            gasto['ano'],
            gasto['mes'],
            gasto['tipoDespesa'],
            gasto.get('valorDocumento', 0),
            gasto.get('valorLiquido', 0),
            gasto.get('nomeFornecedor', ''),
            gasto.get('cnpjCpfFornecedor', ''),
            gasto.get('numeroDocumento', ''),
            gasto.get('dataDocumento', ''),
            gasto.get('urlDocumento', '')
        ))
        
        return True
        
    except Exception as e:
        logger.debug(f"Erro ao salvar gasto: {e}")
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
                WHERE tipo = ? AND ano = ? AND mes = ? AND status = 'in_progress'
            """, (status, total_registros, tipo, ano, mes))
        elif status == 'error':
            cursor.execute("""
                UPDATE coleta_historica 
                SET status = ?, erro = ?, completed_at = CURRENT_TIMESTAMP
                WHERE tipo = ? AND ano = ? AND mes = ? AND status = 'in_progress'
            """, (status, erro, tipo, ano, mes))
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Erro ao registrar coleta: {e}")


def coletar_gastos_historicos(anos=5, limite_deputados=None):
    """
    Coleta histórico de gastos dos últimos N anos
    
    Args:
        anos (int): Número de anos para buscar (padrão: 5)
        limite_deputados (int): Limitar número de deputados para teste (None = todos)
    """
    logger.info("╔═══════════════════════════════════════════════╗")
    logger.info("║  🗄️  COLETA HISTÓRICA DE GASTOS             ║")
    logger.info("╚═══════════════════════════════════════════════╝")
    logger.info("")
    logger.info(f"📅 Período: {anos} anos ({datetime.now().year - anos + 1} - {datetime.now().year})")
    logger.info("")
    
    # Conectar ao banco
    conn = get_connection()
    
    # Buscar deputados
    deputados = buscar_todos_deputados()
    
    if limite_deputados:
        deputados = deputados[:limite_deputados]
        logger.info(f"⚠️  Modo teste: Limitado a {limite_deputados} deputados")
    
    # Salvar deputados no banco
    logger.info("💾 Salvando deputados no banco...")
    for deputado in deputados:
        salvar_deputado(conn, deputado)
    conn.commit()
    logger.info(f"✅ {len(deputados)} deputados salvos\n")
    
    # Calcular período
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month
    ano_inicio = ano_atual - anos + 1
    
    total_gastos = 0
    total_requisicoes = 0
    erro_count = 0
    
    # Para cada ano
    for ano in range(ano_inicio, ano_atual + 1):
        mes_fim = mes_atual if ano == ano_atual else 12
        
        logger.info(f"📊 Coletando ano {ano}...")
        
        # Para cada mês
        for mes in range(1, mes_fim + 1):
            gastos_mes = 0
            
            # Registrar início da coleta
            registrar_coleta(conn, 'gastos', ano, mes, 'in_progress')
            
            # Para cada deputado
            for i, deputado in enumerate(deputados, 1):
                deputado_id = deputado['id']
                
                # Buscar gastos
                gastos = buscar_gastos_deputado(deputado_id, ano, mes)
                total_requisicoes += 1
                
                # Salvar gastos
                for gasto in gastos:
                    if salvar_gasto(conn, deputado_id, gasto):
                        gastos_mes += 1
                        total_gastos += 1
                
                # Commit a cada 10 deputados
                if i % 10 == 0:
                    conn.commit()
                    logger.info(f"   {ano}/{mes:02d} - Progresso: {i}/{len(deputados)} deputados ({gastos_mes} gastos)")
                
                # Rate limiting (100 req/min = 1 req a cada 0.6s)
                if total_requisicoes % 100 == 0:
                    logger.info(f"   ⏸️  Pausa para respeitar rate limit...")
                    time.sleep(60)
            
            # Commit final do mês
            conn.commit()
            registrar_coleta(conn, 'gastos', ano, mes, 'completed', gastos_mes)
            
            logger.info(f"   ✅ {ano}/{mes:02d}: {gastos_mes} gastos coletados")
    
    conn.close()
    
    logger.info("")
    logger.info("╔═══════════════════════════════════════════════╗")
    logger.info("║  ✅ COLETA CONCLUÍDA                         ║")
    logger.info("╚═══════════════════════════════════════════════╝")
    logger.info("")
    logger.info(f"📊 Estatísticas:")
    logger.info(f"   • Total de gastos coletados: {total_gastos}")
    logger.info(f"   • Total de requisições: {total_requisicoes}")
    logger.info(f"   • Deputados processados: {len(deputados)}")
    logger.info(f"   • Período: {ano_inicio}-{ano_atual}")
    logger.info("")
    logger.info(f"💾 Banco de dados: {DATABASE_FILE}")
    logger.info(f"📊 Tamanho: {Path(DATABASE_FILE).stat().st_size / 1024 / 1024:.2f} MB")
    logger.info("")


if __name__ == '__main__':
    import sys
    
    # Modo teste (10 deputados)
    if len(sys.argv) > 1 and sys.argv[1] == '--teste':
        logger.info("🧪 Modo TESTE: Apenas 10 deputados, últimos 2 anos")
        coletar_gastos_historicos(anos=2, limite_deputados=10)
    else:
        # Modo completo
        coletar_gastos_historicos(anos=5)

