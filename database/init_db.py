"""
Inicialização do Banco de Dados - Monitor PL Brasil
Cria e inicializa o banco SQLite com o schema completo
"""
import sqlite3
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Caminhos
BASE_DIR = Path(__file__).parent.parent
DATABASE_DIR = BASE_DIR / 'database'
DATABASE_FILE = DATABASE_DIR / 'monitor_pl.db'
SCHEMA_FILE = DATABASE_DIR / 'schema.sql'


def create_database():
    """Cria o banco de dados e aplica o schema"""
    logger.info("🗄️  Iniciando criação do banco de dados...")
    
    # Criar diretório se não existir
    DATABASE_DIR.mkdir(exist_ok=True)
    
    # Verificar se schema existe
    if not SCHEMA_FILE.exists():
        logger.error(f"❌ Arquivo schema.sql não encontrado: {SCHEMA_FILE}")
        return False
    
    try:
        # Conectar ao banco (cria se não existir)
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        logger.info(f"📂 Banco de dados: {DATABASE_FILE}")
        
        # Ler e executar schema
        logger.info("📝 Aplicando schema...")
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        cursor.executescript(schema_sql)
        conn.commit()
        
        # Verificar tabelas criadas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"✅ {len(tabelas)} tabelas criadas:")
        for tabela in sorted(tabelas):
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor.fetchone()[0]
            logger.info(f"   • {tabela}: {count} registros")
        
        # Verificar views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"✅ {len(views)} views criadas:")
        for view in sorted(views):
            logger.info(f"   • {view}")
        
        conn.close()
        
        logger.info("🎉 Banco de dados criado com sucesso!")
        logger.info(f"📊 Tamanho do banco: {os.path.getsize(DATABASE_FILE) / 1024:.2f} KB")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar banco de dados: {e}")
        return False


def get_connection():
    """Retorna uma conexão com o banco de dados"""
    if not DATABASE_FILE.exists():
        logger.warning("⚠️  Banco de dados não existe. Criando...")
        create_database()
    
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return conn


def get_statistics():
    """Retorna estatísticas gerais do banco"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM vw_estatisticas_gerais")
        stats = dict(cursor.fetchone())
        
        conn.close()
        return stats
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return {}


def reset_database():
    """Remove e recria o banco de dados (CUIDADO!)"""
    logger.warning("⚠️  ATENÇÃO: Resetando banco de dados...")
    
    if DATABASE_FILE.exists():
        logger.info(f"🗑️  Removendo banco existente: {DATABASE_FILE}")
        os.remove(DATABASE_FILE)
    
    return create_database()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        print("\n╔═══════════════════════════════════════════════╗")
        print("║   ⚠️  RESET DO BANCO DE DADOS                ║")
        print("╚═══════════════════════════════════════════════╝\n")
        
        resposta = input("Tem certeza que deseja resetar o banco? (sim/não): ")
        if resposta.lower() == 'sim':
            reset_database()
        else:
            print("❌ Operação cancelada")
    else:
        print("\n╔═══════════════════════════════════════════════╗")
        print("║   🗄️  INICIALIZAÇÃO DO BANCO DE DADOS       ║")
        print("╚═══════════════════════════════════════════════╝\n")
        
        if create_database():
            print("\n📊 Estatísticas do Banco:\n")
            stats = get_statistics()
            for key, value in stats.items():
                print(f"   • {key}: {value}")
            
            print("\n✅ Banco de dados pronto para uso!")
            print(f"   Localização: {DATABASE_FILE}")
        else:
            print("\n❌ Falha na inicialização do banco de dados")
            sys.exit(1)

