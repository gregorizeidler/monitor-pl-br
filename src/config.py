"""
Configuração centralizada do Monitor PL Brasil.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Diretórios
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"

# API URLs
CAMARA_API_BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
SENADO_RSS_URL = "https://www12.senado.leg.br/noticias/feed"
CAMARA_RSS_URL = "https://www.camara.leg.br/noticias/rss/ultimas-noticias"
STF_RSS_URL = "http://www.stf.jus.br/portal/cms/verNoticiaRss.asp"
TSE_RSS_URL = "https://www.tse.jus.br/imprensa/noticias-tse/feed"
AGENCIA_BRASIL_RSS_URL = "https://agenciabrasil.ebc.com.br/rss/ultimas/feed.xml"

# Rate Limiting
MAX_REQUESTS_PER_MINUTE = 30
RETRY_MAX_ATTEMPTS = 3
RETRY_WAIT_EXPONENTIAL_MULTIPLIER = 1
RETRY_WAIT_EXPONENTIAL_MAX = 10

# Twitter/X Credentials
X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET", "")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Sentry
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

# Database
DATABASE_PATH = DATABASE_DIR / "monitor_pl.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# IDs dos deputados monitorados
DEPUTADOS_MONITORADOS = [
    74173,   # Adail Filho (REPUBLICANOS-AM)
    220599,  # Afonso Motta (PDT-RS)
    74693,   # Alexandre Frota (UNIÃO-SP)
    204554,  # André Figueiredo (PDT-CE)
    74693,   # Cabo Gilberto Silva (PL-PB)
    204554,  # Capitão Alberto Neto (PL-AM)
    74173,   # Coronel Tadeu (PL-SP)
    220599,  # Darci de Matos (PSD-SC)
    74693,   # Eduardo Bolsonaro (PL-SP)
    204554,  # Felipe Francischini (UNIÃO-PR)
    74173,   # Filipe Barros (PL-PR)
    220599,  # Greyce Elias (AVANTE-MG)
    74693,   # Julian Lemos (PL-PB)
    204554,  # Luiz Philippe de Orleans e Bragança (PL-SP)
    74173,   # Nikolas Ferreira (PL-MG)
]

# Timeouts
HTTP_TIMEOUT = 30
API_TIMEOUT = 60

# Projeto de Lei
PL_IMPORTANCIA_MIN = 1
PL_IMPORTANCIA_MAX = 5

# Medidas Provisórias
MP_PRAZO_DIAS = 120
MP_DIAS_ALERTA_CRITICO = 30
MP_DIAS_ALERTA_ATENCAO = 60

# Validação
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

if not DATABASE_DIR.exists():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

