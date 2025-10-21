"""
Configuração de monitoramento com Sentry.
"""
import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from src.config import SENTRY_DSN, LOG_LEVEL

logger = logging.getLogger(__name__)


def init_sentry():
    """
    Inicializa Sentry para monitoramento de erros.
    """
    if not SENTRY_DSN:
        logger.warning("SENTRY_DSN não configurado. Monitoramento desabilitado.")
        return
    
    # Configuração de logging para Sentry
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Captura logs INFO e acima
        event_level=logging.ERROR  # Envia eventos para ERROR e acima
    )
    
    try:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[sentry_logging],
            
            # Configurações de performance
            traces_sample_rate=0.1,  # 10% das transações
            
            # Configurações de ambiente
            environment="production",
            
            # Release tracking
            release="monitor-pl@1.0.0",
            
            # Filtros de eventos
            before_send=filter_sensitive_data,
            
            # Configurações adicionais
            attach_stacktrace=True,
            send_default_pii=False,  # Não envia PII por padrão
        )
        
        logger.info("✅ Sentry inicializado com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar Sentry: {e}")


def filter_sensitive_data(event, hint):
    """
    Filtra dados sensíveis antes de enviar ao Sentry.
    
    Args:
        event: Evento do Sentry
        hint: Informações adicionais
        
    Returns:
        Event modificado ou None para não enviar
    """
    # Remove tokens e credenciais
    if 'request' in event:
        if 'headers' in event['request']:
            headers = event['request']['headers']
            for key in ['Authorization', 'X-Api-Key', 'Cookie']:
                if key in headers:
                    headers[key] = '[FILTERED]'
    
    # Remove query params sensíveis
    if 'request' in event and 'query_string' in event['request']:
        sensitive_params = ['token', 'key', 'password', 'secret']
        query = event['request']['query_string']
        for param in sensitive_params:
            if param in query.lower():
                event['request']['query_string'] = '[FILTERED]'
                break
    
    return event


def capture_exception(exception: Exception, context: dict = None):
    """
    Captura exceção e envia ao Sentry com contexto adicional.
    
    Args:
        exception: Exceção para capturar
        context: Dicionário com contexto adicional
    """
    if not SENTRY_DSN:
        return
    
    try:
        with sentry_sdk.push_scope() as scope:
            # Adiciona contexto
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            # Captura exceção
            sentry_sdk.capture_exception(exception)
            
    except Exception as e:
        logger.error(f"Erro ao capturar exceção no Sentry: {e}")


def capture_message(message: str, level: str = "info", context: dict = None):
    """
    Envia mensagem ao Sentry.
    
    Args:
        message: Mensagem para enviar
        level: Nível (debug, info, warning, error, fatal)
        context: Contexto adicional
    """
    if not SENTRY_DSN:
        return
    
    try:
        with sentry_sdk.push_scope() as scope:
            if context:
                for key, value in context.items():
                    scope.set_context(key, value)
            
            sentry_sdk.capture_message(message, level=level)
            
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem ao Sentry: {e}")


def set_user(user_id: str, email: str = None, username: str = None):
    """
    Define informações do usuário para contexto.
    
    Args:
        user_id: ID do usuário
        email: Email (opcional)
        username: Username (opcional)
    """
    if not SENTRY_DSN:
        return
    
    try:
        sentry_sdk.set_user({
            "id": user_id,
            "email": email,
            "username": username
        })
    except Exception as e:
        logger.error(f"Erro ao definir usuário no Sentry: {e}")


def add_breadcrumb(message: str, category: str = "default", level: str = "info", data: dict = None):
    """
    Adiciona breadcrumb para rastreamento.
    
    Args:
        message: Mensagem do breadcrumb
        category: Categoria
        level: Nível
        data: Dados adicionais
    """
    if not SENTRY_DSN:
        return
    
    try:
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data or {}
        )
    except Exception as e:
        logger.error(f"Erro ao adicionar breadcrumb: {e}")

