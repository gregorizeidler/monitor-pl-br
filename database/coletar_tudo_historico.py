"""
Script Mestre - Coleta Histórica Completa
Executa todos os coletores históricos em sequência
"""
import logging
import time
import sys
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.init_db import get_connection, get_statistics, DATABASE_FILE
from database.coletor_historico_gastos import coletar_gastos_historico
from database.coletor_historico_pls import coletar_pls_historico
from database.coletor_historico_votacoes import coletar_votacoes_historico
from database.coletor_historico_mps import coletar_mps_historico

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def mostrar_banner():
    """Mostra banner inicial"""
    print("\n" + "="*70)
    print("║" + " "*68 + "║")
    print("║" + "  🚀 COLETA HISTÓRICA COMPLETA - MONITOR PL BRASIL  ".center(68) + "║")
    print("║" + " "*68 + "║")
    print("="*70 + "\n")


def mostrar_progresso(etapa, total_etapas, descricao):
    """Mostra progresso visual"""
    progresso = int((etapa / total_etapas) * 50)
    barra = "█" * progresso + "░" * (50 - progresso)
    percentual = (etapa / total_etapas) * 100
    
    print(f"\n[{barra}] {percentual:.1f}%")
    print(f"Etapa {etapa}/{total_etapas}: {descricao}\n")


def mostrar_estatisticas_finais():
    """Mostra estatísticas finais do banco"""
    print("\n" + "="*70)
    print("║" + " "*68 + "║")
    print("║" + "  📊 ESTATÍSTICAS FINAIS DO BANCO DE DADOS  ".center(68) + "║")
    print("║" + " "*68 + "║")
    print("="*70 + "\n")
    
    stats = get_statistics()
    
    print(f"👥 Deputados: {stats.get('total_deputados', 0):,}")
    print(f"💰 Gastos: {stats.get('total_gastos', 0):,} registros")
    if stats.get('valor_total_gastos'):
        print(f"   Total gasto: R$ {stats['valor_total_gastos']:,.2f}")
    print(f"📋 Projetos de Lei: {stats.get('total_pls', 0):,}")
    print(f"🗳️  Votações: {stats.get('total_votacoes', 0):,}")
    print(f"⚡ Medidas Provisórias: {stats.get('total_mps', 0):,}")
    print(f"📰 Notícias: {stats.get('total_noticias', 0):,}")
    
    if stats.get('ano_inicio_gastos'):
        print(f"\n📅 Período de gastos: {stats['ano_inicio_gastos']} - {stats['ano_fim_gastos']}")
    
    tamanho_mb = Path(DATABASE_FILE).stat().st_size / 1024 / 1024
    print(f"\n💾 Tamanho do banco: {tamanho_mb:.2f} MB")
    print(f"📂 Localização: {DATABASE_FILE}")
    
    print("\n" + "="*70 + "\n")


def main(modo_teste=False, anos=5):
    """
    Executa coleta histórica completa
    
    Args:
        modo_teste (bool): Se True, coleta apenas uma amostra pequena
        anos (int): Número de anos para coletar
    """
    inicio = time.time()
    
    mostrar_banner()
    
    if modo_teste:
        logger.warning("⚠️  MODO TESTE ATIVO")
        logger.warning("    Coletando apenas uma amostra pequena dos dados")
        logger.warning("    Para coleta completa, rode sem o parâmetro --teste")
        print()
    
    logger.info(f"📋 Plano de Coleta ({anos} anos):")
    logger.info("   1. Gastos Parlamentares")
    logger.info("   2. Projetos de Lei")
    logger.info("   3. Votações")
    logger.info("   4. Medidas Provisórias")
    logger.info("")
    
    if not modo_teste:
        logger.info("⏱️  Tempo estimado: 2-4 horas")
        logger.info("")
        input("Pressione ENTER para iniciar a coleta...")
        print()
    
    resultados = {}
    
    # Etapa 1: Gastos
    mostrar_progresso(1, 4, "Coletando gastos parlamentares")
    try:
        if modo_teste:
            coletar_gastos_historico(anos_historico=1, teste_modo=True, max_deputies_teste=5)
        else:
            coletar_gastos_historico(anos_historico=anos)
        resultados['gastos'] = '✅'
    except Exception as e:
        logger.error(f"❌ Erro na coleta de gastos: {e}")
        resultados['gastos'] = '❌'
    
    # Etapa 2: PLs
    mostrar_progresso(2, 4, "Coletando Projetos de Lei")
    try:
        if modo_teste:
            coletar_pls_historico(anos_historico=1, teste_modo=True, max_pls_teste=20)
        else:
            coletar_pls_historico(anos_historico=anos)
        resultados['pls'] = '✅'
    except Exception as e:
        logger.error(f"❌ Erro na coleta de PLs: {e}")
        resultados['pls'] = '❌'
    
    # Etapa 3: Votações
    mostrar_progresso(3, 4, "Coletando Votações")
    try:
        if modo_teste:
            coletar_votacoes_historico(anos_historico=1, teste_modo=True, max_votes_teste=30)
        else:
            coletar_votacoes_historico(anos_historico=anos)
        resultados['votacoes'] = '✅'
    except Exception as e:
        logger.error(f"❌ Erro na coleta de votações: {e}")
        resultados['votacoes'] = '❌'
    
    # Etapa 4: MPs
    mostrar_progresso(4, 4, "Coletando Medidas Provisórias")
    try:
        if modo_teste:
            coletar_mps_historico(anos_historico=1, teste_modo=True, max_mps_teste=20)
        else:
            coletar_mps_historico(anos_historico=anos)
        resultados['mps'] = '✅'
    except Exception as e:
        logger.error(f"❌ Erro na coleta de MPs: {e}")
        resultados['mps'] = '❌'
    
    # Estatísticas finais
    tempo_total = time.time() - inicio
    horas = int(tempo_total // 3600)
    minutos = int((tempo_total % 3600) // 60)
    segundos = int(tempo_total % 60)
    
    print("\n" + "="*70)
    print("║" + " "*68 + "║")
    print("║" + "  🎉 COLETA HISTÓRICA CONCLUÍDA!  ".center(68) + "║")
    print("║" + " "*68 + "║")
    print("="*70)
    
    print(f"\n⏱️  Tempo total: {horas}h {minutos}m {segundos}s\n")
    
    print("📊 Resultados:")
    print(f"   {resultados.get('gastos', '❓')} Gastos Parlamentares")
    print(f"   {resultados.get('pls', '❓')} Projetos de Lei")
    print(f"   {resultados.get('votacoes', '❓')} Votações")
    print(f"   {resultados.get('mps', '❓')} Medidas Provisórias")
    print()
    
    mostrar_estatisticas_finais()
    
    logger.info("✅ Próximos passos:")
    logger.info("   1. Os dados estão salvos no banco SQLite")
    logger.info("   2. Acesse o chatbot em: http://localhost:3001/chat")
    logger.info("   3. Ou explore os dados com queries SQL")
    logger.info("")
    logger.info(f"💡 Para explorar: sqlite3 {DATABASE_FILE}")
    
    return True


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Coletar dados históricos completos')
    parser.add_argument('--teste', action='store_true', help='Modo teste: coleta apenas amostra')
    parser.add_argument('--anos', type=int, default=5, help='Número de anos para coletar (padrão: 5)')
    
    args = parser.parse_args()
    
    try:
        main(modo_teste=args.teste, anos=args.anos)
    except KeyboardInterrupt:
        print("\n\n⚠️  Coleta interrompida pelo usuário")
        print("   O progresso foi salvo e você pode retomar depois")
    except Exception as e:
        logger.error(f"❌ Erro na coleta: {e}")
        import traceback
        traceback.print_exc()
