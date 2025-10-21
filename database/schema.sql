-- Monitor PL Brasil - Database Schema
-- SQLite Database for Historical Data
-- ============================================

-- Tabela de Deputados
CREATE TABLE IF NOT EXISTS deputados (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    partido TEXT,
    uf TEXT,
    email TEXT,
    data_nascimento DATE,
    sexo TEXT,
    legislatura_atual INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para deputados
CREATE INDEX IF NOT EXISTS idx_deputados_nome ON deputados(nome);
CREATE INDEX IF NOT EXISTS idx_deputados_partido ON deputados(partido);
CREATE INDEX IF NOT EXISTS idx_deputados_uf ON deputados(uf);

-- Tabela de Gastos Parlamentares
CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deputado_id INTEGER NOT NULL,
    ano INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    tipo_despesa TEXT NOT NULL,
    valor_documento REAL NOT NULL,
    valor_liquido REAL NOT NULL,
    fornecedor TEXT,
    cnpj_fornecedor TEXT,
    numero_documento TEXT,
    data_documento DATE,
    url_documento TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deputado_id) REFERENCES deputados(id)
);

-- Índices para gastos
CREATE INDEX IF NOT EXISTS idx_gastos_deputado ON gastos(deputado_id);
CREATE INDEX IF NOT EXISTS idx_gastos_ano_mes ON gastos(ano, mes);
CREATE INDEX IF NOT EXISTS idx_gastos_tipo ON gastos(tipo_despesa);
CREATE INDEX IF NOT EXISTS idx_gastos_data ON gastos(data_documento);

-- Tabela de Projetos de Lei
CREATE TABLE IF NOT EXISTS projetos_lei (
    id INTEGER PRIMARY KEY,
    numero TEXT NOT NULL UNIQUE,
    ano INTEGER NOT NULL,
    ementa TEXT,
    autor_id INTEGER,
    autor_nome TEXT,
    tipo TEXT DEFAULT 'PL',
    data_apresentacao DATE,
    status TEXT,
    categoria TEXT,
    importancia INTEGER DEFAULT 1,
    tramitacao TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para PLs
CREATE INDEX IF NOT EXISTS idx_pls_numero ON projetos_lei(numero);
CREATE INDEX IF NOT EXISTS idx_pls_ano ON projetos_lei(ano);
CREATE INDEX IF NOT EXISTS idx_pls_autor ON projetos_lei(autor_id);
CREATE INDEX IF NOT EXISTS idx_pls_data ON projetos_lei(data_apresentacao);
CREATE INDEX IF NOT EXISTS idx_pls_categoria ON projetos_lei(categoria);
CREATE INDEX IF NOT EXISTS idx_pls_status ON projetos_lei(status);

-- Tabela de Votações
CREATE TABLE IF NOT EXISTS votacoes (
    id TEXT PRIMARY KEY,
    data TIMESTAMP NOT NULL,
    descricao TEXT,
    proposicao TEXT,
    votos_sim INTEGER DEFAULT 0,
    votos_nao INTEGER DEFAULT 0,
    votos_outros INTEGER DEFAULT 0,
    aprovacao BOOLEAN,
    importancia INTEGER DEFAULT 1,
    orgao TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para votações
CREATE INDEX IF NOT EXISTS idx_votacoes_data ON votacoes(data);
CREATE INDEX IF NOT EXISTS idx_votacoes_aprovacao ON votacoes(aprovacao);
CREATE INDEX IF NOT EXISTS idx_votacoes_importancia ON votacoes(importancia);

-- Tabela de Votos de Deputados (detalhamento de cada votação)
CREATE TABLE IF NOT EXISTS votos_deputados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    votacao_id TEXT NOT NULL,
    deputado_id INTEGER NOT NULL,
    voto TEXT NOT NULL, -- 'Sim', 'Não', 'Abstenção', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (votacao_id) REFERENCES votacoes(id),
    FOREIGN KEY (deputado_id) REFERENCES deputados(id)
);

-- Índices para votos de deputados
CREATE INDEX IF NOT EXISTS idx_votos_votacao ON votos_deputados(votacao_id);
CREATE INDEX IF NOT EXISTS idx_votos_deputado ON votos_deputados(deputado_id);
CREATE INDEX IF NOT EXISTS idx_votos_tipo ON votos_deputados(voto);

-- Tabela de Medidas Provisórias
CREATE TABLE IF NOT EXISTS medidas_provisorias (
    id INTEGER PRIMARY KEY,
    numero TEXT NOT NULL UNIQUE,
    ano INTEGER NOT NULL,
    ementa TEXT,
    data_apresentacao DATE,
    prazo_vencimento DATE,
    dias_restantes INTEGER,
    nivel_urgencia INTEGER DEFAULT 1,
    status TEXT,
    categoria TEXT,
    importancia INTEGER DEFAULT 1,
    aprovacao BOOLEAN,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para MPs
CREATE INDEX IF NOT EXISTS idx_mps_numero ON medidas_provisorias(numero);
CREATE INDEX IF NOT EXISTS idx_mps_ano ON medidas_provisorias(ano);
CREATE INDEX IF NOT EXISTS idx_mps_data ON medidas_provisorias(data_apresentacao);
CREATE INDEX IF NOT EXISTS idx_mps_urgencia ON medidas_provisorias(nivel_urgencia);
CREATE INDEX IF NOT EXISTS idx_mps_status ON medidas_provisorias(status);

-- Tabela de Notícias (histórico)
CREATE TABLE IF NOT EXISTS noticias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    link TEXT UNIQUE NOT NULL,
    fonte TEXT NOT NULL,
    data_publicacao TIMESTAMP,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para notícias
CREATE INDEX IF NOT EXISTS idx_noticias_fonte ON noticias(fonte);
CREATE INDEX IF NOT EXISTS idx_noticias_data ON noticias(data_publicacao);
CREATE INDEX IF NOT EXISTS idx_noticias_posted ON noticias(posted_at);

-- Tabela de Coleta (controle de progresso)
CREATE TABLE IF NOT EXISTS coleta_historica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL, -- 'gastos', 'pls', 'votacoes', 'mps'
    ano INTEGER NOT NULL,
    mes INTEGER,
    status TEXT DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'error'
    total_registros INTEGER DEFAULT 0,
    erro TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para controle de coleta
CREATE INDEX IF NOT EXISTS idx_coleta_tipo ON coleta_historica(tipo);
CREATE INDEX IF NOT EXISTS idx_coleta_status ON coleta_historica(status);
CREATE INDEX IF NOT EXISTS idx_coleta_ano ON coleta_historica(ano);

-- View: Ranking de Gastos por Deputado (últimos 12 meses)
CREATE VIEW IF NOT EXISTS vw_ranking_gastos_12m AS
SELECT 
    d.id,
    d.nome,
    d.partido,
    d.uf,
    SUM(g.valor_liquido) as total_gasto,
    COUNT(g.id) as total_despesas,
    AVG(g.valor_liquido) as media_despesa,
    MAX(g.data_documento) as ultima_despesa
FROM deputados d
LEFT JOIN gastos g ON d.id = g.deputado_id
WHERE g.data_documento >= date('now', '-12 months')
GROUP BY d.id, d.nome, d.partido, d.uf
ORDER BY total_gasto DESC;

-- View: PLs por Categoria e Ano
CREATE VIEW IF NOT EXISTS vw_pls_por_categoria_ano AS
SELECT 
    ano,
    categoria,
    COUNT(*) as total,
    SUM(CASE WHEN status LIKE '%Aprovad%' THEN 1 ELSE 0 END) as aprovados,
    ROUND(AVG(importancia), 2) as importancia_media
FROM projetos_lei
GROUP BY ano, categoria
ORDER BY ano DESC, total DESC;

-- View: Taxa de Aprovação por Votação
CREATE VIEW IF NOT EXISTS vw_taxa_aprovacao_votacoes AS
SELECT 
    DATE(data) as data,
    COUNT(*) as total_votacoes,
    SUM(CASE WHEN aprovacao = 1 THEN 1 ELSE 0 END) as aprovadas,
    SUM(CASE WHEN aprovacao = 0 THEN 1 ELSE 0 END) as rejeitadas,
    ROUND(100.0 * SUM(CASE WHEN aprovacao = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as taxa_aprovacao
FROM votacoes
GROUP BY DATE(data)
ORDER BY data DESC;

-- View: Estatísticas Gerais do Banco
CREATE VIEW IF NOT EXISTS vw_estatisticas_gerais AS
SELECT 
    (SELECT COUNT(*) FROM deputados) as total_deputados,
    (SELECT COUNT(*) FROM gastos) as total_gastos,
    (SELECT SUM(valor_liquido) FROM gastos) as valor_total_gastos,
    (SELECT COUNT(*) FROM projetos_lei) as total_pls,
    (SELECT COUNT(*) FROM votacoes) as total_votacoes,
    (SELECT COUNT(*) FROM medidas_provisorias) as total_mps,
    (SELECT COUNT(*) FROM noticias) as total_noticias,
    (SELECT MIN(ano) FROM gastos) as ano_inicio_gastos,
    (SELECT MAX(ano) FROM gastos) as ano_fim_gastos;

-- Trigger: Atualizar timestamp em deputados
CREATE TRIGGER IF NOT EXISTS update_deputados_timestamp 
AFTER UPDATE ON deputados
BEGIN
    UPDATE deputados SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger: Atualizar timestamp em projetos_lei
CREATE TRIGGER IF NOT EXISTS update_pls_timestamp 
AFTER UPDATE ON projetos_lei
BEGIN
    UPDATE projetos_lei SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger: Atualizar timestamp em medidas_provisorias
CREATE TRIGGER IF NOT EXISTS update_mps_timestamp 
AFTER UPDATE ON medidas_provisorias
BEGIN
    UPDATE medidas_provisorias SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================
-- Schema Version Control
-- ============================================
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR IGNORE INTO schema_version (version, description) 
VALUES (1, 'Schema inicial com todas as tabelas, índices e views');

