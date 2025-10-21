"""Coletor de Medidas Provisórias."""
import logging
import requests
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
HEADERS = {"Accept": "application/json"}


def fetch_active_mps(max_mps=50):
    """
    Busca Medidas Provisórias ativas (em tramitação).
    
    Args:
        max_mps (int): Número máximo de MPs a retornar.
    
    Returns:
        list: Lista de MPs ativas.
    """
    logger.info("Buscando Medidas Provisórias ativas...")
    
    try:
        url = f"{BASE_URL}/proposicoes"
        params = {
            'siglaTipo': 'MPV',
            'ordem': 'DESC',
            'ordenarPor': 'id',
            'itens': max_mps
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        mps = []
        for mp in data.get('dados', []):
            mps.append({
                'id': mp['id'],
                'numero': mp['numero'],
                'ano': mp['ano'],
                'ementa': mp['ementa'],
                'uri': mp['uri']
            })
        
        logger.info(f"Encontradas {len(mps)} MPs.")
        return mps
    
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar MPs: {e}")
        return []


def get_mp_details(mp_id):
    """
    Busca detalhes completos de uma MP.
    
    Args:
        mp_id (int): ID da MP.
    
    Returns:
        dict: Detalhes da MP.
    """
    logger.info(f"Buscando detalhes da MP {mp_id}...")
    
    try:
        url = f"{BASE_URL}/proposicoes/{mp_id}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        mp = data.get('dados', {})
        status = mp.get('statusProposicao', {})
        
        return {
            'id': mp['id'],
            'numero': f"MPV {mp['numero']}/{mp['ano']}",
            'ementa': mp['ementa'],
            'data_apresentacao': mp.get('dataApresentacao', ''),
            'status': {
                'data': status.get('dataHora', ''),
                'descricao': status.get('descricaoTramitacao', ''),
                'situacao': status.get('descricaoSituacao', ''),
                'orgao': status.get('siglaOrgao', '')
            },
            'url_inteiro_teor': mp.get('urlInteiroTeor', ''),
            'uri_autores': mp.get('uriAutores', '')
        }
    
    except requests.RequestException as e:
        logger.error(f"Erro ao buscar detalhes da MP {mp_id}: {e}")
        return None


def calculate_mp_urgency(mp_details):
    """
    Calcula urgência de uma MP baseado no prazo constitucional.
    
    MPs têm 120 dias para serem votadas (60 + 60 de prorrogação).
    
    Args:
        mp_details (dict): Detalhes da MP.
    
    Returns:
        dict: Informações de urgência.
    """
    data_apresentacao_str = mp_details.get('data_apresentacao', '')
    
    if not data_apresentacao_str:
        return {
            'dias_restantes': None,
            'nivel_urgencia': 0,
            'prazo_vencido': False
        }
    
    try:
        data_apresentacao = datetime.fromisoformat(data_apresentacao_str.replace('Z', '+00:00'))
        data_apresentacao = data_apresentacao.replace(tzinfo=None)
        
        hoje = datetime.now()
        dias_decorridos = (hoje - data_apresentacao).days
        dias_restantes = 120 - dias_decorridos
        
        # Determinar nível de urgência
        if dias_restantes < 0:
            nivel = 5  # Vencido
            prazo_vencido = True
        elif dias_restantes <= 10:
            nivel = 5  # Crítico
            prazo_vencido = False
        elif dias_restantes <= 30:
            nivel = 4  # Urgente
            prazo_vencido = False
        elif dias_restantes <= 60:
            nivel = 3  # Atenção
            prazo_vencido = False
        elif dias_restantes <= 90:
            nivel = 2  # Normal
            prazo_vencido = False
        else:
            nivel = 1  # Recente
            prazo_vencido = False
        
        return {
            'dias_restantes': dias_restantes,
            'nivel_urgencia': nivel,
            'prazo_vencido': prazo_vencido,
            'data_apresentacao': data_apresentacao_str
        }
    
    except (ValueError, AttributeError) as e:
        logger.error(f"Erro ao calcular urgência: {e}")
        return {
            'dias_restantes': None,
            'nivel_urgencia': 0,
            'prazo_vencido': False
        }


def classify_mp_importance(mp_details):
    """
    Classifica importância de uma MP.
    
    Args:
        mp_details (dict): Detalhes da MP.
    
    Returns:
        tuple: (importancia [1-5], categoria)
    """
    ementa = mp_details['ementa'].lower()
    
    # Palavras-chave de alta importância
    keywords_high = [
        'orçamento', 'tributário', 'imposto', 'tributo',
        'previdência', 'salário mínimo', 'reforma',
        'calamidade', 'emergência', 'crédito extraordinário'
    ]
    
    # Palavras-chave de média importância
    keywords_medium = [
        'servidor público', 'funcionalismo',
        'educação', 'saúde', 'segurança',
        'transporte', 'infraestrutura'
    ]
    
    # Categorias
    categories = {
        'economia': ['orçamento', 'tributário', 'imposto', 'fiscal', 'financeiro', 'tributo'],
        'previdência': ['previdência', 'aposentadoria', 'inss'],
        'saúde': ['saúde', 'sus', 'medicamento'],
        'educação': ['educação', 'escola', 'universidade'],
        'emergência': ['calamidade', 'emergência', 'extraordinário'],
        'trabalho': ['trabalho', 'trabalhador', 'salário'],
    }
    
    # Determinar importância
    importancia = 2
    for keyword in keywords_high:
        if keyword in ementa:
            importancia = 5
            break
    
    if importancia == 2:
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
    print("--- Testando o coletor de Medidas Provisórias ---\n")
    
    # Buscar MPs ativas
    print("1. Buscando MPs ativas...")
    mps = fetch_active_mps(max_mps=10)
    
    if mps:
        print(f"\nEncontradas {len(mps)} MPs.\n")
        
        # Buscar detalhes das primeiras 3
        print("2. Analisando primeiras MPs...\n")
        
        for mp in mps[:3]:
            print(f"{'='*60}")
            detalhes = get_mp_details(mp['id'])
            
            if detalhes:
                print(f"📋 {detalhes['numero']}")
                print(f"Ementa: {detalhes['ementa'][:100]}...")
                
                # Calcular urgência
                urgencia = calculate_mp_urgency(detalhes)
                if urgencia['dias_restantes'] is not None:
                    if urgencia['prazo_vencido']:
                        print(f"⚠️  PRAZO VENCIDO há {abs(urgencia['dias_restantes'])} dias!")
                    else:
                        print(f"⏰ Dias restantes: {urgencia['dias_restantes']}")
                    print(f"🚨 Urgência: {urgencia['nivel_urgencia']}/5")
                
                # Classificar importância
                importancia, categoria = classify_mp_importance(detalhes)
                print(f"⭐ Importância: {importancia}/5")
                print(f"🏷️  Categoria: {categoria}")
                print(f"📍 Status: {detalhes['status']['descricao']}")
                print()
    else:
        print("Nenhuma MP encontrada.")
    
    print("\n" + "-" * 50)

