"""Coletor de Votações da Câmara dos Deputados."""
import logging
import requests
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"Accept": "application/json"}


def fetch_recent_votes(days=7, max_votes=20):
    """
    Busca votações recentes da Câmara dos Deputados.
    
    Args:
        days (int): Número de dias para buscar votações retroativamente.
        max_votes (int): Número máximo de votações a retornar.
    
    Returns:
        list: Lista de dicionários com informações das votações.
    """
    logger.info(f"Buscando votações dos últimos {days} dias...")
    
    try:
        data_inicio = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        url = f"{BASE_URL}/votacoes"
        params = {
            'dataInicio': data_inicio,
            'ordem': 'DESC',
            'ordenarPor': 'dataHoraRegistro',
            'itens': max_votes
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        votacoes = []
        for votacao in data.get('dados', []):
            votacoes.append({
                'id': votacao.get('id', ''),
                'data': votacao.get('dataHoraRegistro', ''),
                'descricao': votacao.get('descricao', ''),
                'sigla_orgao': votacao.get('siglaOrgao', ''),
                'uri_proposicao': votacao.get('uriProposicaoObjeto', ''),
                'uri': votacao.get('uri', '')
            })
        
        logger.info(f"Encontradas {len(votacoes)} votações.")
        return votacoes
    
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar votações: {e}")
        return []


def get_vote_details(vote_id):
    """
    Busca detalhes completos de uma votação específica.
    
    Args:
        vote_id (str): ID da votação.
    
    Returns:
        dict: Dicionário com detalhes completos da votação.
    """
    logger.info(f"Buscando detalhes da votação {vote_id}...")
    
    try:
        url = f"{BASE_URL}/votacoes/{vote_id}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        votacao = data.get('dados', {})
        
        # Buscar os votos individuais para contar manualmente
        votos_sim = 0
        votos_nao = 0
        votos_outros = 0
        
        try:
            url_votos = f"{BASE_URL}/votacoes/{vote_id}/votos"
            response_votos = requests.get(url_votos, headers=HEADERS, timeout=15)
            response_votos.raise_for_status()
            dados_votos = response_votos.json()
            
            for voto in dados_votos.get('dados', []):
                tipo_voto = voto.get('tipoVoto', '').lower()
                if tipo_voto == 'sim':
                    votos_sim += 1
                elif tipo_voto == 'não' or tipo_voto == 'nao':
                    votos_nao += 1
                else:
                    votos_outros += 1
                    
            logger.info(f"Placar contado: {votos_sim} SIM, {votos_nao} NÃO, {votos_outros} OUTROS")
        except Exception as e:
            logger.warning(f"Erro ao contar votos: {e}. Usando placares da API se disponíveis.")
            # Fallback para campos da API se existirem
            votos_sim = votacao.get('placarSim', 0)
            votos_nao = votacao.get('placarNao', 0)
            votos_outros = votacao.get('placarOutros', 0)
        
        # Determinar aprovação baseado no placar
        aprovacao = None
        if votos_sim > votos_nao:
            aprovacao = True
        elif votos_nao > votos_sim:
            aprovacao = False
        
        return {
            'id': votacao.get('id', ''),
            'data': votacao.get('dataHoraRegistro', ''),
            'descricao': votacao.get('descricao', ''),
            'sigla_orgao': votacao.get('siglaOrgao', ''),
            'aprovacao': aprovacao,
            'votos_sim': votos_sim,
            'votos_nao': votos_nao,
            'votos_outros': votos_outros,
            'proposicao_id': votacao.get('proposicaoObjeto', {}).get('id', ''),
            'proposicao_numero': votacao.get('proposicaoObjeto', {}).get('descricao', ''),
            'uri_votos': votacao.get('uriVotos', '')
        }
    
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar detalhes da votação {vote_id}: {e}")
        return None


def get_vote_orientation_by_party(vote_id):
    """
    Busca orientação de voto por partido.
    
    Args:
        vote_id (str): ID da votação.
    
    Returns:
        list: Lista de orientações por partido.
    """
    try:
        url = f"{BASE_URL}/votacoes/{vote_id}/orientacoes"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        orientacoes = []
        for orientacao in data.get('dados', []):
            orientacoes.append({
                'partido': orientacao.get('siglaPartidoBloco', ''),
                'orientacao': orientacao.get('orientacaoVoto', '')
            })
        
        return orientacoes
    
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar orientações da votação {vote_id}: {e}")
        return []


def get_deputies_votes(vote_id):
    """
    Busca como cada deputado votou.
    
    Args:
        vote_id (str): ID da votação.
    
    Returns:
        list: Lista com voto de cada deputado.
    """
    try:
        url = f"{BASE_URL}/votacoes/{vote_id}/votos"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        votos = []
        for voto in data.get('dados', []):
            deputado = voto.get('deputado_', {})
            votos.append({
                'deputado_id': deputado.get('id', ''),
                'deputado_nome': deputado.get('nome', ''),
                'partido': deputado.get('siglaPartido', ''),
                'uf': deputado.get('siglaUf', ''),
                'voto': voto.get('tipoVoto', '')
            })
        
        return votos
    
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar votos da votação {vote_id}: {e}")
        return []


def classify_vote_importance(vote_details):
    """
    Classifica a importância de uma votação.
    
    Args:
        vote_details (dict): Detalhes da votação.
    
    Returns:
        int: Importância de 1 a 5.
    """
    descricao = vote_details.get('descricao', '').lower()
    proposicao = vote_details.get('proposicao_numero', '').lower()
    
    # Palavras-chave de alta importância
    keywords_high = [
        'reforma', 'constituição', 'emenda constitucional', 'pec',
        'orçamento', 'ldo', 'loa', 'medida provisória', 'mp',
        'código penal', 'código civil'
    ]
    
    # Palavras-chave de média importância
    keywords_medium = [
        'projeto de lei', 'pl ', 'imposto', 'tributo',
        'saúde', 'educação', 'segurança'
    ]
    
    # Verificar importância
    for keyword in keywords_high:
        if keyword in descricao or keyword in proposicao:
            return 5
    
    for keyword in keywords_medium:
        if keyword in descricao or keyword in proposicao:
            return 3
    
    return 2


if __name__ == '__main__':
    print("--- Testando o coletor de Votações ---\n")
    
    # Buscar votações recentes
    print("1. Buscando votações recentes...")
    votacoes = fetch_recent_votes(days=30, max_votes=5)
    
    if votacoes:
        print(f"\nEncontradas {len(votacoes)} votações.\n")
        
        # Buscar detalhes da primeira votação
        primeira_votacao = votacoes[0]
        print(f"2. Buscando detalhes da votação {primeira_votacao['id']}...")
        
        detalhes = get_vote_details(primeira_votacao['id'])
        if detalhes:
            print(f"\nDescrição: {detalhes['descricao']}")
            print(f"Data: {detalhes['data']}")
            print(f"Placar: {detalhes['votos_sim']} SIM | {detalhes['votos_nao']} NÃO | {detalhes['votos_outros']} OUTROS")
            print(f"Resultado: {'APROVADO' if detalhes['aprovacao'] else 'REJEITADO' if detalhes['aprovacao'] is False else 'N/A'}")
            
            # Classificar importância
            importancia = classify_vote_importance(detalhes)
            print(f"Importância: {importancia}/5 ⭐")
            
            # Buscar orientações
            print(f"\n3. Buscando orientações partidárias...")
            orientacoes = get_vote_orientation_by_party(primeira_votacao['id'])
            if orientacoes:
                print("\nOrientações:")
                for ori in orientacoes[:5]:
                    print(f"  {ori['partido']}: {ori['orientacao']}")
    else:
        print("Nenhuma votação encontrada.")
    
    print("\n" + "-" * 50)

