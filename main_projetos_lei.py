"""
Monitor PL Brasil - Bot de Acompanhamento de Projetos de Lei

Este script monitora projetos de lei da Câmara dos Deputados,
classifica por importância e posta threads informativas no X.
"""
import logging
from datetime import datetime, timezone

# Importando funções dos módulos criados
from src.coletores.coleta_projetos_lei import (
    fetch_recent_projects,
    get_project_details,
    get_project_authors,
    classify_project_importance
)
from src.analisador.analisador_projetos import (
    prune_old_tracked_projects,
    filter_new_projects,
    detect_status_changes,
    select_project_to_post,
    should_post_project
)
from src.formatadores.formatador_projetos import format_project_thread

# Importando funções do código já existente
from src.api_client import post_tweet
from src.main import load_json, save_json

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

STATE_FILE = 'estado.json'


def main():
    """Função principal do bot de projetos de lei."""
    logging.info("--- Iniciando ciclo do Bot de Projetos de Lei ---")
    
    # 1. Carregar e limpar o estado
    state = load_json(STATE_FILE) or {}
    tracked_projects = state.get('tracked_projects', [])
    pruned_projects = prune_old_tracked_projects(tracked_projects, days_to_keep=30)
    state['tracked_projects'] = pruned_projects
    
    # 2. Buscar projetos recentes da API
    logging.info("Buscando projetos de lei recentes...")
    recent_projects = fetch_recent_projects(days=7, max_projects=30)
    
    if not recent_projects:
        logging.info("Nenhum projeto encontrado. Encerrando ciclo.")
        return
    
    # 3. Enriquecer projetos com detalhes completos
    logging.info("Enriquecendo dados dos projetos...")
    enriched_projects = []
    
    for project in recent_projects[:10]:  # Limitar para não sobrecarregar a API
        details = get_project_details(project['id'])
        if details:
            # Classificar importância
            importancia, categoria = classify_project_importance(details)
            details['importancia'] = importancia
            details['categoria'] = categoria
            enriched_projects.append(details)
    
    if not enriched_projects:
        logging.info("Nenhum projeto com detalhes completos. Encerrando ciclo.")
        return
    
    # 4. Filtrar novos projetos e detectar mudanças
    logging.info("Analisando projetos...")
    new_projects = filter_new_projects(enriched_projects, state['tracked_projects'])
    changed_projects = detect_status_changes(enriched_projects, state['tracked_projects'])
    
    logging.info(
        "Análise concluída: %d novos projetos, %d com mudanças",
        len(new_projects),
        len(changed_projects)
    )
    
    # 5. Selecionar projeto para postar
    selected_project = select_project_to_post(
        new_projects,
        changed_projects,
        min_importance=3  # Apenas projetos com importância >= 3
    )
    
    if not selected_project:
        logging.info("Nenhum projeto relevante para postar. Encerrando ciclo.")
        return
    
    # 6. Verificar se deve postar
    if not should_post_project(selected_project, state['tracked_projects'], max_posts_per_day=3):
        logging.info("Critérios de postagem não atendidos. Encerrando ciclo.")
        return
    
    # 7. Buscar autores do projeto
    logging.info("Buscando autores do projeto %s...", selected_project['numero'])
    autores = get_project_authors(selected_project['id'])
    
    # 8. Formatar thread
    logging.info("Formatando thread para o projeto %s...", selected_project['numero'])
    change_type = 'status_change' if 'change_type' in selected_project else 'new'
    thread_content = format_project_thread(selected_project, autores, change_type)
    
    # 9. Postar a thread no X
    logging.info("Postando thread no X...")
    last_tweet_id = None
    post_successful = True
    
    for tweet in thread_content:
        result = post_tweet(tweet, reply_to_id=last_tweet_id)
        
        if result == "duplicate":
            logging.warning("Tweet duplicado detectado. O projeto será marcado como postado.")
            post_successful = True
            break
        
        if not result:
            logging.error("Falha ao postar tweet. Abortando thread.")
            post_successful = False
            break
        
        last_tweet_id = result
    
    # 10. Atualizar estado se a postagem foi bem-sucedida
    if post_successful:
        logging.info("Thread postada com sucesso!")
        
        # Criar registro do projeto rastreado
        tracked_item = {
            'id': selected_project['id'],
            'numero': selected_project['numero'],
            'last_status': selected_project['status'].get('descricao_tramitacao', ''),
            'tracked_at': datetime.now(timezone.utc).isoformat(),
            'posted': True,
            'importancia': selected_project.get('importancia', 1),
            'categoria': selected_project.get('categoria', 'diversos')
        }
        
        # Atualizar projeto existente ou adicionar novo
        project_exists = False
        for i, tracked in enumerate(state['tracked_projects']):
            if tracked['id'] == selected_project['id']:
                state['tracked_projects'][i] = tracked_item
                project_exists = True
                break
        
        if not project_exists:
            state['tracked_projects'].append(tracked_item)
        
        # Salvar estado
        save_json(state, STATE_FILE)
        logging.info("Estado atualizado com o novo projeto rastreado.")
    else:
        logging.error("A postagem da thread falhou. O estado não foi alterado.")
    
    logging.info("--- Ciclo do Bot de Projetos de Lei finalizado ---")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error("Erro crítico no bot de projetos de lei: %s", e, exc_info=True)
        raise

