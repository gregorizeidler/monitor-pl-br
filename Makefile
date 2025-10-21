# Makefile para Monitor PL Brasil
# ================================

.PHONY: help install test lint format docker clean

# Variáveis
PYTHON := python3
PIP := pip3
PYTEST := pytest
DOCKER_COMPOSE := docker-compose

# Cores para output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Mostra esta ajuda
	@echo "$(CYAN)Monitor PL Brasil - Comandos Disponíveis$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Instala dependências Python
	@echo "$(CYAN)Instalando dependências Python...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Dependências instaladas$(NC)"

install-dev: ## Instala dependências de desenvolvimento
	@echo "$(CYAN)Instalando dependências de desenvolvimento...$(NC)"
	$(PIP) install -r requirements.txt
	cd dashboard && npm install
	@echo "$(GREEN)✅ Dependências de dev instaladas$(NC)"

test: ## Roda todos os testes
	@echo "$(CYAN)Rodando testes...$(NC)"
	$(PYTEST) -v
	@echo "$(GREEN)✅ Testes concluídos$(NC)"

test-cov: ## Roda testes com coverage
	@echo "$(CYAN)Rodando testes com coverage...$(NC)"
	$(PYTEST) --cov=src --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✅ Coverage report gerado em htmlcov/$(NC)"

test-watch: ## Roda testes em modo watch
	@echo "$(CYAN)Modo watch ativado...$(NC)"
	$(PYTEST) -f

lint: ## Roda linters
	@echo "$(CYAN)Rodando linters...$(NC)"
	$(PYTHON) -m pylint src/
	@echo "$(GREEN)✅ Linting concluído$(NC)"

format: ## Formata código com black
	@echo "$(CYAN)Formatando código...$(NC)"
	$(PYTHON) -m black src/ tests/
	@echo "$(GREEN)✅ Código formatado$(NC)"

docker-build: ## Build das imagens Docker
	@echo "$(CYAN)Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✅ Imagens construídas$(NC)"

docker-up: ## Inicia containers
	@echo "$(CYAN)Iniciando containers...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Containers rodando$(NC)"

docker-down: ## Para containers
	@echo "$(CYAN)Parando containers...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Containers parados$(NC)"

docker-logs: ## Mostra logs dos containers
	$(DOCKER_COMPOSE) logs -f

docker-clean: ## Remove containers, volumes e imagens
	@echo "$(YELLOW)⚠️  Removendo todos os containers e volumes...$(NC)"
	$(DOCKER_COMPOSE) down -v --rmi all
	@echo "$(GREEN)✅ Limpeza completa$(NC)"

run-backend: ## Roda backend Python
	@echo "$(CYAN)Iniciando backend...$(NC)"
	$(PYTHON) -m src.main

run-dashboard: ## Roda dashboard Next.js
	@echo "$(CYAN)Iniciando dashboard...$(NC)"
	cd dashboard && npm run dev

collect-data: ## Coleta dados (rápido)
	@echo "$(CYAN)Coletando dados...$(NC)"
	$(PYTHON) coletar_todos_dados.py
	@echo "$(GREEN)✅ Dados coletados$(NC)"

collect-history: ## Coleta histórico completo (demora)
	@echo "$(YELLOW)⚠️  Isso pode demorar 2-4 horas...$(NC)"
	$(PYTHON) database/coletar_tudo_historico.py --anos 5

init-db: ## Inicializa banco de dados
	@echo "$(CYAN)Inicializando banco de dados...$(NC)"
	$(PYTHON) database/init_db.py
	@echo "$(GREEN)✅ Banco inicializado$(NC)"

clean: ## Remove arquivos temporários
	@echo "$(CYAN)Limpando arquivos temporários...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	@echo "$(GREEN)✅ Limpeza concluída$(NC)"

setup: install init-db ## Setup completo do projeto
	@echo "$(CYAN)Setup completo...$(NC)"
	@echo "$(GREEN)✅ Projeto configurado com sucesso!$(NC)"
	@echo ""
	@echo "$(CYAN)Próximos passos:$(NC)"
	@echo "  1. Configure o arquivo .env com suas credenciais"
	@echo "  2. Rode 'make run-dashboard' para iniciar o dashboard"
	@echo "  3. Acesse http://localhost:3001"

.DEFAULT_GOAL := help

