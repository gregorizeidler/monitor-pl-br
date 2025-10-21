"""Módulo para formatar projetos de lei em threads para redes sociais."""
import logging
import textwrap

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_TWEET_LENGTH = 280


def format_project_thread(project_details, autores=None, change_type=None):
    """
    Formata um projeto de lei em uma thread para o Twitter/X.
    
    Args:
        project_details (dict): Detalhes completos do projeto.
        autores (list): Lista de autores do projeto.
        change_type (str): Tipo de mudança, se houver ('new' ou 'status_change').
    
    Returns:
        list: Lista de strings, cada uma é um tweet da thread.
    """
    numero = project_details['numero']
    ementa = project_details['ementa'].strip().strip('"')
    status_info = project_details.get('status', {})
    importancia = project_details.get('importancia', 1)
    categoria = project_details.get('categoria', 'diversos')
    
    # Emojis por categoria
    emoji_map = {
        'economia': '💰',
        'saúde': '🏥',
        'educação': '📚',
        'segurança': '👮',
        'trabalho': '👷',
        'meio ambiente': '🌳',
        'diversos': '📋'
    }
    
    emoji_categoria = emoji_map.get(categoria, '📋')
    
    # Emoji de importância
    emoji_importancia = '⭐' * min(importancia, 5)
    
    thread = []
    
    # --- Tweet 1: Cabeçalho ---
    if change_type == 'status_change':
        old_status = project_details.get('old_status', '')
        new_status = project_details.get('new_status', '')
        header = f"🔄 ATUALIZAÇÃO DE PROJETO DE LEI\n\n{emoji_categoria} {numero}"
        tweet1 = f"{header}\n\n{emoji_importancia}\n\n"
        tweet1 += f"Status mudou:\n📍 De: {old_status[:50]}\n📍 Para: {new_status[:50]}"
    else:
        header = f"🆕 NOVO PROJETO DE LEI\n\n{emoji_categoria} {numero}"
        tweet1 = f"{header}\n\n{emoji_importancia}"
    
    # Adicionar hashtag e footer
    tweet1 += "\n\n👇 Siga o fio para detalhes\n#MonitorPL #ProjetoDeLei #Legislação"
    
    # Garantir que cabe em 280 caracteres
    if len(tweet1) > MAX_TWEET_LENGTH:
        tweet1 = tweet1[:MAX_TWEET_LENGTH-3] + "..."
    
    thread.append(tweet1)
    
    # --- Tweet 2: Ementa ---
    tweet2 = f"📄 O QUE O PROJETO QUER:\n\n"
    
    # Limitar ementa para caber no tweet
    available_space = MAX_TWEET_LENGTH - len(tweet2) - 30  # Reserva espaço
    ementa_shortened = textwrap.shorten(ementa, width=available_space, placeholder="...")
    tweet2 += ementa_shortened
    
    thread.append(tweet2)
    
    # --- Tweet 3: Autoria e Status ---
    tweet3 = ""
    
    if autores:
        autores_str = ', '.join(autores[:2])  # Máximo 2 autores
        if len(autores) > 2:
            autores_str += f" e outros {len(autores) - 2}"
        tweet3 += f"✍️ Autor(es):\n{autores_str}\n\n"
    
    situacao = status_info.get('situacao', 'Em tramitação')
    orgao = status_info.get('orgao', '')
    
    tweet3 += f"📊 Status atual:\n{situacao}"
    if orgao:
        tweet3 += f"\n🏛️ Órgão: {orgao}"
    
    # Adicionar categoria
    tweet3 += f"\n\n🏷️ Tema: {categoria.title()}"
    
    thread.append(tweet3)
    
    # --- Tweet 4: Link e fonte ---
    url_projeto = f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={project_details['id']}"
    
    tweet4 = f"🔗 Acompanhe a tramitação:\n{url_projeto}\n\n"
    tweet4 += "📋 Dados oficiais da Câmara dos Deputados\n"
    tweet4 += "#TransparenciaBrasil #Fiscalize"
    
    thread.append(tweet4)
    
    logging.info("Thread formatada para o projeto: %s", numero)
    return thread


def format_summary_thread(projects_count, important_count, categories):
    """
    Formata uma thread com resumo dos projetos da semana.
    
    Args:
        projects_count (int): Total de projetos analisados.
        important_count (int): Projetos importantes detectados.
        categories (dict): Dicionário com contagem por categoria.
    
    Returns:
        list: Lista de tweets.
    """
    thread = []
    
    # Tweet 1: Resumo geral
    tweet1 = "📊 RESUMO SEMANAL - PROJETOS DE LEI\n\n"
    tweet1 += f"🔢 Total analisado: {projects_count}\n"
    tweet1 += f"⭐ Importantes: {important_count}\n\n"
    tweet1 += "👇 Veja os detalhes\n#MonitorPL"
    
    thread.append(tweet1)
    
    # Tweet 2: Por categoria
    if categories:
        tweet2 = "📋 PROJETOS POR TEMA:\n\n"
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        
        emoji_map = {
            'economia': '💰',
            'saúde': '🏥',
            'educação': '📚',
            'segurança': '👮',
            'trabalho': '👷',
            'meio ambiente': '🌳',
            'diversos': '📋'
        }
        
        for cat, count in sorted_cats[:5]:  # Top 5 categorias
            emoji = emoji_map.get(cat, '📋')
            tweet2 += f"{emoji} {cat.title()}: {count}\n"
        
        thread.append(tweet2)
    
    # Tweet 3: Call to action
    tweet3 = "💡 Quer saber sobre algum projeto específico?\n\n"
    tweet3 += "Todos os dados são públicos e verificáveis.\n\n"
    tweet3 += "🔗 camara.leg.br\n\n"
    tweet3 += "#TransparênciaBrasil #Fiscalize"
    
    thread.append(tweet3)
    
    return thread


if __name__ == '__main__':
    print("--- Testando o formatador de projetos ---\n")
    
    # Simular detalhes de um projeto
    sample_project = {
        'id': 2573075,
        'numero': 'PL 5264/2025',
        'ementa': (
            'Altera a legislação para incluir os profissionais do magistério da '
            'educação básica no rol de categorias com direito a adicionais de '
            'insalubridade e/ou periculosidade, conforme o caso.'
        ),
        'data_apresentacao': '2025-10-16T18:51',
        'status': {
            'data': '2025-10-16T18:51',
            'descricao_tramitacao': 'Apresentação de Proposição',
            'despacho': 'Apresentação do PL',
            'situacao': 'Aguardando análise',
            'orgao': 'MESA'
        },
        'importancia': 4,
        'categoria': 'educação'
    }
    
    sample_autores = [
        'Dr. Fernando Máximo (UNIÃO-RO)',
        'Maria Silva (PT-SP)'
    ]
    
    print("1. Formatando thread para novo projeto...")
    thread_new = format_project_thread(sample_project, sample_autores, 'new')
    
    print(f"\n--- THREAD COMPLETA ({len(thread_new)} tweets) ---\n")
    for i, tweet in enumerate(thread_new):
        print(f"--- TWEET {i+1}/{len(thread_new)} (Tamanho: {len(tweet)}) ---")
        print(tweet)
        print()
    
    print("-" * 50)
    
    print("\n2. Formatando thread para mudança de status...")
    sample_project['old_status'] = 'Aguardando análise'
    sample_project['new_status'] = 'Aprovado em Comissão de Educação'
    
    thread_change = format_project_thread(sample_project, sample_autores, 'status_change')
    
    print(f"\n--- THREAD DE ATUALIZAÇÃO ---")
    print(f"TWEET 1:\n{thread_change[0]}\n")
    
    print("-" * 50)
    
    print("\n3. Formatando resumo semanal...")
    categories = {
        'educação': 15,
        'saúde': 12,
        'economia': 10,
        'segurança': 8,
        'diversos': 5
    }
    
    thread_summary = format_summary_thread(50, 20, categories)
    
    print(f"\n--- RESUMO SEMANAL ({len(thread_summary)} tweets) ---\n")
    for i, tweet in enumerate(thread_summary):
        print(f"TWEET {i+1}:\n{tweet}\n")
    
    print("-" * 50)

