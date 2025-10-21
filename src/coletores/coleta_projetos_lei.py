"""Coletor de Projetos de Lei da Câmara dos Deputados."""
import logging
import requests
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URLs da API de Dados Abertos da Câmara
BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"Accept": "application/json"}


def fetch_recent_projects(days=7, max_projects=50):
    """
    Busca projetos de lei apresentados ou atualizados recentemente.
    
    Args:
        days (int): Número de dias para buscar projetos retroativamente.
        max_projects (int): Número máximo de projetos a retornar.
    
    Returns:
        list: Lista de dicionários com informações dos projetos.
    """
    logging.info("Buscando projetos de lei dos últimos %d dias...", days)
    
    try:
        # Data inicial para filtrar
        data_inicio = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Buscar proposições recentes (PLs)
        url = f"{BASE_URL}/proposicoes"
        params = {
            'siglaTipo': 'PL',  # Apenas Projetos de Lei
            'dataInicio': data_inicio,
            'ordem': 'DESC',
            'ordenarPor': 'id',
            'itens': max_projects
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        projects = []
        for prop in data.get('dados', []):
            projects.append({
                'id': prop['id'],
                'numero': prop['numero'],
                'ano': prop['ano'],
                'tipo': prop['siglaTipo'],
                'ementa': prop['ementa'],
                'uri': prop['uri'],
                'data_apresentacao': prop.get('dataApresentacao', '')
            })
        
        logging.info("Encontrados %d projetos de lei.", len(projects))
        return projects
    
    except requests.RequestException as e:
        logging.error("Erro ao buscar projetos de lei: %s", e)
        return []


def get_project_details(project_id):
    """
    Busca detalhes completos de um projeto específico.
    
    Args:
        project_id (int): ID do projeto na API da Câmara.
    
    Returns:
        dict: Dicionário com detalhes completos do projeto ou None em caso de erro.
    """
    logging.info("Buscando detalhes do projeto %d...", project_id)
    
    try:
        url = f"{BASE_URL}/proposicoes/{project_id}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        projeto = data.get('dados', {})
        status = projeto.get('statusProposicao', {})
        
        return {
            'id': projeto['id'],
            'numero': f"{projeto['siglaTipo']} {projeto['numero']}/{projeto['ano']}",
            'ementa': projeto['ementa'],
            'data_apresentacao': projeto.get('dataApresentacao', ''),
            'status': {
                'data': status.get('dataHora', ''),
                'descricao_tramitacao': status.get('descricaoTramitacao', ''),
                'despacho': status.get('despacho', ''),
                'situacao': status.get('descricaoSituacao', 'Em tramitação'),
                'orgao': status.get('siglaOrgao', '')
            },
            'url_inteiro_teor': projeto.get('urlInteiroTeor', ''),
            'uri_autores': projeto.get('uriAutores', '')
        }
    
    except requests.RequestException as e:
        logging.error("Erro ao buscar detalhes do projeto %d: %s", project_id, e)
        return None


def get_project_authors(project_id):
    """
    Busca os autores de um projeto de lei.
    
    Args:
        project_id (int): ID do projeto na API da Câmara.
    
    Returns:
        list: Lista de nomes dos autores.
    """
    try:
        url = f"{BASE_URL}/proposicoes/{project_id}/autores"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        autores = []
        for autor in data.get('dados', []):
            nome = autor.get('nome', '')
            partido = autor.get('siglaPartido', '')
            uf = autor.get('siglaUf', '')
            
            if nome:
                autor_str = nome
                if partido and uf:
                    autor_str += f" ({partido}-{uf})"
                autores.append(autor_str)
        
        return autores[:3]  # Retorna no máximo 3 autores principais
    
    except requests.RequestException as e:
        logging.error("Erro ao buscar autores do projeto %d: %s", project_id, e)
        return []


def get_project_tramitacoes(project_id, limit=5):
    """
    Busca as últimas tramitações de um projeto.
    
    Args:
        project_id (int): ID do projeto na API da Câmara.
        limit (int): Número máximo de tramitações a retornar.
    
    Returns:
        list: Lista das últimas tramitações.
    """
    try:
        url = f"{BASE_URL}/proposicoes/{project_id}/tramitacoes"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        tramitacoes = []
        for tram in data.get('dados', [])[:limit]:
            tramitacoes.append({
                'data': tram.get('dataHora', ''),
                'descricao': tram.get('descricaoTramitacao', ''),
                'orgao': tram.get('siglaOrgao', ''),
                'despacho': tram.get('despacho', '')
            })
        
        return tramitacoes
    
    except requests.RequestException as e:
        logging.error("Erro ao buscar tramitações do projeto %d: %s", project_id, e)
        return []


def classify_project_importance(project_details):
    """
    Classifica a importância de um projeto com base em palavras-chave.
    
    Args:
        project_details (dict): Detalhes do projeto.
    
    Returns:
        tuple: (importancia [1-5], categoria)
    """
    ementa = project_details['ementa'].lower()
    
    # Palavras-chave de alta importância
    keywords_high = [
        'constituição', 'código penal', 'código civil', 'reforma tributária',
        'previdência', 'sus', 'salário mínimo', 'educação básica',
        'segurança pública', 'meio ambiente'
    ]
    
    # Palavras-chave de média importância
    keywords_medium = [
        'imposto', 'trabalho', 'servidor público', 'aposentadoria',
        'saúde', 'escola', 'universidade', 'polícia'
    ]
    
    # Categorias
    categories = {
        'economia': ['imposto', 'tributário', 'orçamento', 'fiscal', 'financeiro'],
        'saúde': ['sus', 'saúde', 'medicamento', 'vacina', 'hospital'],
        'educação': ['educação', 'escola', 'universidade', 'professor', 'ensino'],
        'segurança': ['segurança', 'polícia', 'crime', 'penal', 'prisão'],
        'trabalho': ['trabalho', 'trabalhador', 'emprego', 'salário', 'clt'],
        'meio ambiente': ['meio ambiente', 'ambiental', 'clima', 'desmatamento'],
    }
    
    # Determinar importância
    importancia = 1
    for keyword in keywords_high:
        if keyword in ementa:
            importancia = 5
            break
    
    if importancia == 1:
        for keyword in keywords_medium:
            if keyword in ementa:
                importancia = 3
                break
    
    # Determinar categoria
    categoria = 'diversos'
    for cat, keywords in categories.items():
        for keyword in keywords:
            if keyword in ementa:
                categoria = cat
                break
        if categoria != 'diversos':
            break
    
    return importancia, categoria


if __name__ == '__main__':
    print("--- Testando o coletor de Projetos de Lei ---\n")
    
    # Testar busca de projetos recentes
    print("1. Buscando projetos recentes...")
    projects = fetch_recent_projects(days=7, max_projects=5)
    
    if projects:
        print(f"\nEncontrados {len(projects)} projetos.\n")
        
        # Testar detalhes de um projeto
        primeiro_projeto = projects[0]
        print(f"2. Buscando detalhes do {primeiro_projeto['tipo']} {primeiro_projeto['numero']}/{primeiro_projeto['ano']}...")
        
        detalhes = get_project_details(primeiro_projeto['id'])
        if detalhes:
            print(f"\nNúmero: {detalhes['numero']}")
            print(f"Ementa: {detalhes['ementa'][:100]}...")
            print(f"Status: {detalhes['status']['descricao_tramitacao']}")
            
            # Testar autores
            print(f"\n3. Buscando autores...")
            autores = get_project_authors(primeiro_projeto['id'])
            print(f"Autores: {', '.join(autores)}")
            
            # Testar classificação
            print(f"\n4. Classificando importância...")
            importancia, categoria = classify_project_importance(detalhes)
            print(f"Importância: {importancia}/5")
            print(f"Categoria: {categoria}")
    else:
        print("Nenhum projeto encontrado.")
    
    print("\n" + "-" * 50)

