"""
Modelos de dados com validação Pydantic.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class Deputado(BaseModel):
    """Modelo de dados para Deputado."""
    id: int = Field(..., gt=0, description="ID único do deputado")
    nome: str = Field(..., min_length=1, max_length=200, description="Nome completo")
    partido: str = Field(..., min_length=1, max_length=50, description="Sigla do partido")
    uf: str = Field(..., min_length=2, max_length=2, description="UF do estado")
    email: Optional[str] = Field(None, description="Email do deputado")
    
    @field_validator('uf')
    @classmethod
    def validate_uf(cls, v: str) -> str:
        """Valida se a UF é válida."""
        ufs_validas = [
            'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
            'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
            'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
        ]
        if v.upper() not in ufs_validas:
            raise ValueError(f"UF inválida: {v}")
        return v.upper()


class Gasto(BaseModel):
    """Modelo de dados para Gasto Parlamentar."""
    deputado_id: int = Field(..., gt=0, description="ID do deputado")
    ano: int = Field(..., ge=2000, le=2100, description="Ano do gasto")
    mes: int = Field(..., ge=1, le=12, description="Mês do gasto")
    tipo_despesa: str = Field(..., min_length=1, description="Tipo da despesa")
    valor_documento: float = Field(..., ge=0, description="Valor do documento")
    valor_liquido: float = Field(..., ge=0, description="Valor líquido")
    fornecedor: Optional[str] = Field(None, description="Nome do fornecedor")
    data_documento: str = Field(..., description="Data do documento")


class ProjetoLei(BaseModel):
    """Modelo de dados para Projeto de Lei."""
    id: int = Field(..., gt=0, description="ID único do PL")
    numero: str = Field(..., min_length=1, description="Número do PL (ex: PL 1234/2024)")
    ano: int = Field(..., ge=1988, le=2100, description="Ano do PL")
    ementa: str = Field(..., min_length=10, description="Ementa do PL")
    tipo: str = Field(default="PL", description="Tipo da proposição")
    categoria: str = Field(..., description="Categoria do PL")
    importancia: int = Field(..., ge=1, le=5, description="Importância (1-5)")
    status: str = Field(..., description="Status de tramitação")
    data_apresentacao: Optional[str] = Field(None, description="Data de apresentação")
    
    @field_validator('categoria')
    @classmethod
    def validate_categoria(cls, v: str) -> str:
        """Valida categorias conhecidas."""
        categorias_validas = [
            'economia', 'saúde', 'educação', 'segurança', 'trabalho',
            'meio ambiente', 'transporte', 'tecnologia', 'diversos'
        ]
        v_lower = v.lower()
        if v_lower not in categorias_validas:
            return 'diversos'
        return v_lower


class Votacao(BaseModel):
    """Modelo de dados para Votação."""
    id: str = Field(..., min_length=1, description="ID único da votação")
    data: str = Field(..., description="Data e hora da votação")
    descricao: str = Field(..., min_length=1, description="Descrição da votação")
    proposicao: str = Field(..., description="Proposição votada")
    votos_sim: int = Field(..., ge=0, description="Votos Sim")
    votos_nao: int = Field(..., ge=0, description="Votos Não")
    votos_outros: int = Field(..., ge=0, description="Outros votos")
    aprovacao: Optional[bool] = Field(None, description="Se foi aprovada")
    importancia: int = Field(default=3, ge=1, le=5, description="Importância (1-5)")


class MedidaProvisoria(BaseModel):
    """Modelo de dados para Medida Provisória."""
    id: int = Field(..., gt=0, description="ID único da MP")
    numero: str = Field(..., min_length=1, description="Número da MP")
    ementa: str = Field(..., min_length=10, description="Ementa da MP")
    data_apresentacao: str = Field(..., description="Data de apresentação")
    status: str = Field(..., description="Status atual")
    dias_restantes: int = Field(..., ge=-999, description="Dias restantes (pode ser negativo)")
    prazo_vencido: bool = Field(..., description="Se o prazo venceu")
    nivel_urgencia: int = Field(..., ge=1, le=5, description="Nível de urgência (1-5)")
    importancia: int = Field(..., ge=1, le=5, description="Importância (1-5)")
    categoria: str = Field(..., description="Categoria da MP")


class Noticia(BaseModel):
    """Modelo de dados para Notícia."""
    titulo: str = Field(..., min_length=1, max_length=500, description="Título da notícia")
    link: str = Field(..., min_length=1, description="URL da notícia")
    data_publicacao: str = Field(..., description="Data de publicação")
    fonte: str = Field(..., description="Fonte da notícia")
    
    @field_validator('link')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Valida se é uma URL válida."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError(f"URL inválida: {v}")
        return v
    
    @field_validator('fonte')
    @classmethod
    def validate_fonte(cls, v: str) -> str:
        """Valida fontes conhecidas."""
        fontes_validas = ['Senado', 'Câmara', 'STF', 'TSE', 'Agência Brasil']
        if v not in fontes_validas:
            return 'Outros'
        return v


class RankingGastos(BaseModel):
    """Modelo de dados para Ranking de Gastos."""
    ranking: List[dict] = Field(..., description="Lista de deputados com gastos")
    total_deputados: int = Field(..., ge=0, description="Total de deputados")
    total_gasto: float = Field(..., ge=0, description="Total gasto")
    periodo: str = Field(..., description="Período do ranking")

