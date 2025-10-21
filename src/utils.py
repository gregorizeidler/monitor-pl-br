"""
Utilitários gerais do Monitor PL Brasil.
"""
import logging
from typing import Optional, Any, Dict
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
from src.config import (
    RETRY_MAX_ATTEMPTS,
    RETRY_WAIT_EXPONENTIAL_MULTIPLIER,
    RETRY_WAIT_EXPONENTIAL_MAX,
    HTTP_TIMEOUT
)

# Configurar logger
logger = logging.getLogger(__name__)


class APIError(Exception):
    """Exceção customizada para erros de API."""
    pass


class ValidationError(Exception):
    """Exceção customizada para erros de validação."""
    pass


@retry(
    stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
    wait=wait_exponential(
        multiplier=RETRY_WAIT_EXPONENTIAL_MULTIPLIER,
        max=RETRY_WAIT_EXPONENTIAL_MAX
    ),
    retry=retry_if_exception_type((requests.RequestException, requests.Timeout)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def fetch_with_retry(
    url: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = HTTP_TIMEOUT
) -> requests.Response:
    """
    Faz requisição HTTP com retry automático.
    
    Args:
        url: URL para fazer a requisição
        method: Método HTTP (GET, POST, etc)
        params: Query parameters
        json_data: Dados JSON para enviar no body
        headers: Headers customizados
        timeout: Timeout em segundos
        
    Returns:
        Response object do requests
        
    Raises:
        APIError: Se a API retornar erro após todas as tentativas
        requests.RequestException: Para outros erros de rede
    """
    try:
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            headers=headers,
            timeout=timeout
        )
        
        # Loga a requisição
        logger.debug(f"{method} {url} - Status: {response.status_code}")
        
        # Verifica se houve erro HTTP
        response.raise_for_status()
        
        return response
        
    except requests.HTTPError as e:
        logger.error(f"HTTP Error: {e} - URL: {url}")
        raise APIError(f"Erro na API: {e}") from e
        
    except requests.Timeout as e:
        logger.error(f"Timeout: {e} - URL: {url}")
        raise
        
    except requests.RequestException as e:
        logger.error(f"Request Error: {e} - URL: {url}")
        raise


def safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """
    Acessa dicionários aninhados de forma segura.
    
    Args:
        data: Dicionário para acessar
        keys: Chaves para acessar (pode ser aninhado)
        default: Valor padrão se não encontrar
        
    Returns:
        Valor encontrado ou default
        
    Exemplo:
        >>> data = {'a': {'b': {'c': 123}}}
        >>> safe_get(data, 'a', 'b', 'c')
        123
        >>> safe_get(data, 'a', 'x', 'y', default=0)
        0
    """
    try:
        result = data
        for key in keys:
            result = result[key]
        return result
    except (KeyError, TypeError, AttributeError):
        return default


def format_currency(value: float) -> str:
    """
    Formata valor em moeda brasileira.
    
    Args:
        value: Valor numérico
        
    Returns:
        String formatada (ex: "R$ 1.234,56")
    """
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def truncate_text(text: str, max_length: int = 280, suffix: str = "...") -> str:
    """
    Trunca texto mantendo palavras completas.
    
    Args:
        text: Texto para truncar
        max_length: Tamanho máximo
        suffix: Sufixo para adicionar quando truncar
        
    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text
    
    # Trunca e encontra o último espaço
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + suffix


def validate_response_data(
    response: requests.Response,
    expected_keys: Optional[list] = None
) -> dict:
    """
    Valida resposta da API.
    
    Args:
        response: Response object
        expected_keys: Lista de chaves esperadas no JSON
        
    Returns:
        Dados JSON validados
        
    Raises:
        ValidationError: Se a validação falhar
    """
    try:
        data = response.json()
    except ValueError as e:
        logger.error(f"Resposta não é JSON válido: {e}")
        raise ValidationError("Resposta da API não é JSON válido") from e
    
    if expected_keys:
        missing_keys = [key for key in expected_keys if key not in data]
        if missing_keys:
            logger.error(f"Chaves faltando na resposta: {missing_keys}")
            raise ValidationError(f"Chaves faltando: {missing_keys}")
    
    return data


def setup_logging(level: str = "INFO") -> None:
    """
    Configura logging do sistema.
    
    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    from src.config import LOG_FORMAT
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('monitor_pl.log', encoding='utf-8')
        ]
    )
    
    # Reduz verbosidade de libs externas
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

