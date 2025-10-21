"""Módulo para análise e filtragem de projetos de lei."""
import logging
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def prune_old_tracked_projects(tracked_projects, days_to_keep=30):
    """
    Remove projetos antigos da lista de projetos rastreados.
    
    Args:
        tracked_projects (list): Lista de projetos já rastreados.
        days_to_keep (int): Número de dias para manter um projeto na lista.
    
    Returns:
        list: A lista filtrada de projetos.
    """
    if not tracked_projects:
        return []
    
    pruned_list = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    
    for project in tracked_projects:
        tracked_date = datetime.fromisoformat(project['tracked_at'])
        if tracked_date >= cutoff_date:
            pruned_list.append(project)
        else:
            logging.info("Removendo projeto antigo do estado: PL %s", project['numero'])
    
    return pruned_list


def filter_new_projects(all_projects, tracked_projects):
    """
    Filtra projetos que ainda não foram postados.
    
    Args:
        all_projects (list): Lista de todos os projetos coletados.
        tracked_projects (list): Lista de projetos já rastreados.
    
    Returns:
        list: Lista de projetos novos.
    """
    if not all_projects:
        return []
    
    tracked_ids = {project['id'] for project in tracked_projects}
    new_projects = []
    
    for project in all_projects:
        if project['id'] not in tracked_ids:
            new_projects.append(project)
    
    logging.info("Filtrados %d novos projetos.", len(new_projects))
    return new_projects


def detect_status_changes(current_projects, tracked_projects):
    """
    Detecta mudanças de status em projetos já rastreados.
    
    Args:
        current_projects (list): Lista de projetos atuais com seus detalhes.
        tracked_projects (list): Lista de projetos já rastreados.
    
    Returns:
        list: Lista de projetos que tiveram mudanças importantes.
    """
    changed_projects = []
    
    # Criar índice dos projetos rastreados
    tracked_index = {p['id']: p for p in tracked_projects}
    
    for current in current_projects:
        project_id = current['id']
        
        if project_id in tracked_index:
            tracked = tracked_index[project_id]
            
            # Verificar se o status mudou
            current_status = current.get('status', {}).get('descricao_tramitacao', '')
            tracked_status = tracked.get('last_status', '')
            
            if current_status != tracked_status and current_status:
                logging.info(
                    "Mudança de status detectada no PL %s: '%s' -> '%s'",
                    current['numero'],
                    tracked_status,
                    current_status
                )
                
                # Marcar como mudança importante apenas para certos tipos
                if is_important_status_change(tracked_status, current_status):
                    changed_projects.append({
                        **current,
                        'change_type': 'status_change',
                        'old_status': tracked_status,
                        'new_status': current_status
                    })
    
    return changed_projects


def is_important_status_change(old_status, new_status):
    """
    Determina se uma mudança de status é importante o suficiente para postar.
    
    Args:
        old_status (str): Status anterior.
        new_status (str): Status novo.
    
    Returns:
        bool: True se a mudança é importante.
    """
    important_keywords = [
        'aprovado', 'rejeitado', 'arquivado', 'sancionado', 'vetado',
        'plenário', 'votação', 'urgência', 'promulgado'
    ]
    
    new_lower = new_status.lower()
    
    for keyword in important_keywords:
        if keyword in new_lower:
            return True
    
    return False


def select_project_to_post(new_projects, changed_projects, min_importance=3):
    """
    Seleciona o projeto mais relevante para postar.
    
    Args:
        new_projects (list): Lista de projetos novos.
        changed_projects (list): Lista de projetos com mudanças.
        min_importance (int): Importância mínima para considerar (1-5).
    
    Returns:
        dict or None: O projeto selecionado ou None se não houver nenhum relevante.
    """
    # Prioridade 1: Projetos com mudanças importantes
    for project in changed_projects:
        importancia = project.get('importancia', 1)
        if importancia >= min_importance:
            logging.info("Selecionado projeto com mudança de status: %s", project['numero'])
            return project
    
    # Prioridade 2: Novos projetos importantes
    for project in new_projects:
        importancia = project.get('importancia', 1)
        if importancia >= min_importance:
            logging.info("Selecionado novo projeto: %s", project['numero'])
            return project
    
    # Prioridade 3: Qualquer mudança
    if changed_projects:
        logging.info("Selecionado projeto com mudança: %s", changed_projects[0]['numero'])
        return changed_projects[0]
    
    # Prioridade 4: Qualquer novo projeto
    if new_projects:
        logging.info("Selecionado novo projeto: %s", new_projects[0]['numero'])
        return new_projects[0]
    
    logging.info("Nenhum projeto relevante encontrado para postar.")
    return None


def should_post_project(project, tracked_projects, max_posts_per_day=5):
    """
    Determina se deve postar sobre um projeto específico.
    
    Args:
        project (dict): O projeto a considerar.
        tracked_projects (list): Lista de projetos já postados.
        max_posts_per_day (int): Máximo de posts por dia.
    
    Returns:
        bool: True se deve postar.
    """
    # Contar quantos projetos foram postados hoje
    today = datetime.now(timezone.utc).date()
    posts_today = 0
    
    for tracked in tracked_projects:
        posted_date = datetime.fromisoformat(tracked['tracked_at']).date()
        if posted_date == today:
            posts_today += 1
    
    if posts_today >= max_posts_per_day:
        logging.info("Limite de posts diários atingido (%d/%d).", posts_today, max_posts_per_day)
        return False
    
    # Verificar importância mínima
    importancia = project.get('importancia', 1)
    if importancia < 2:  # Só posta projetos com importância >= 2
        logging.info("Projeto %s tem importância muito baixa (%d/5).", project['numero'], importancia)
        return False
    
    return True


if __name__ == '__main__':
    print("--- Testando o analisador de projetos ---\n")
    
    # Simular alguns projetos
    tracked = [
        {
            'id': 123,
            'numero': 'PL 1000/2024',
            'last_status': 'Apresentação de Proposição',
            'tracked_at': '2025-10-10T10:00:00+00:00'
        },
        {
            'id': 124,
            'numero': 'PL 1001/2024',
            'last_status': 'Aguardando Análise',
            'tracked_at': '2025-10-15T10:00:00+00:00'
        }
    ]
    
    current = [
        {
            'id': 123,
            'numero': 'PL 1000/2024',
            'status': {'descricao_tramitacao': 'Aprovado em Comissão'},
            'importancia': 4,
            'categoria': 'saúde'
        },
        {
            'id': 125,
            'numero': 'PL 1002/2024',
            'status': {'descricao_tramitacao': 'Apresentação de Proposição'},
            'importancia': 5,
            'categoria': 'economia'
        }
    ]
    
    print("1. Detectando mudanças de status...")
    changes = detect_status_changes(current, tracked)
    print(f"   Mudanças detectadas: {len(changes)}")
    if changes:
        for change in changes:
            print(f"   - {change['numero']}: {change['old_status']} -> {change['new_status']}")
    
    print("\n2. Filtrando novos projetos...")
    new = filter_new_projects(current, tracked)
    print(f"   Novos projetos: {len(new)}")
    if new:
        for proj in new:
            print(f"   - {proj['numero']}")
    
    print("\n3. Selecionando projeto para postar...")
    selected = select_project_to_post(new, changes, min_importance=3)
    if selected:
        print(f"   Selecionado: {selected['numero']} (importância: {selected['importancia']}/5)")
    else:
        print("   Nenhum projeto selecionado.")
    
    print("\n" + "-" * 50)

