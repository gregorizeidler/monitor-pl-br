'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { RefreshCw, TrendingDown, Newspaper, FileText, Calendar, Users, DollarSign } from 'lucide-react';

interface DashboardData {
  gastos: {
    ultimoProcessado: number;
    totalRanking: number;
    topGastadores: Array<{
      nome: string;
      partido: string;
      uf: string;
      totalGasto: number;
    }>;
  };
  noticias: {
    totalPostadas: number;
    ultimaNoticia: {
      link: string;
      posted_at: string;
    } | null;
    recentes: Array<{
      link: string;
      posted_at: string;
    }>;
  };
  projetos: {
    totalRastreados: number;
    porCategoria: Record<string, number>;
    ultimoProjeto: {
      numero: string;
      categoria: string;
      importancia: number;
    } | null;
    recentes: Array<{
      id: number;
      numero: string;
      ementa: string;
      categoria: string;
      importancia: number;
      last_status: string;
      tracked_at: string;
      posted: boolean;
    }>;
  };
  votacoes: {
    totalVotacoes: number;
    recentes: Array<{
      id: string;
      data: string;
      descricao: string;
      proposicao: string;
      votos_sim: number;
      votos_nao: number;
      votos_outros: number;
      aprovacao: boolean | null;
      importancia: number;
    }>;
  };
  medidas_provisorias: {
    totalAtivas: number;
    recentes: Array<{
      id: number;
      numero: string;
      ementa: string;
      dias_restantes: number;
      nivel_urgencia: number;
      prazo_vencido: boolean;
      importancia: number;
      categoria: string;
      status: string;
    }>;
  };
  ultimaAtualizacao: string;
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [countdown, setCountdown] = useState(30);

  const fetchData = async () => {
    try {
      const response = await fetch('/api/dashboard');
      const result = await response.json();
      setData(result);
      setLastUpdate(new Date());
      setCountdown(30);
    } catch (error) {
      console.error('Erro ao buscar dados:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Auto-refresh a cada 30 segundos
    const interval = setInterval(fetchData, 30000);
    
    // Countdown
    const countdownInterval = setInterval(() => {
      setCountdown(prev => prev > 0 ? prev - 1 : 30);
    }, 1000);

    return () => {
      clearInterval(interval);
      clearInterval(countdownInterval);
    };
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(value);
  };

  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-white text-xl">Carregando dados...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-black">
      {/* Header */}
      <header className="bg-black/30 backdrop-blur-lg border-b border-white/10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-white mb-1">
                🏛️ Monitor PL Brasil
              </h1>
              <p className="text-sm text-blue-300">Dashboard em Tempo Real</p>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-2 text-white mb-1">
                <RefreshCw className={`w-4 h-4 ${countdown <= 5 ? 'animate-spin' : ''}`} />
                <span className="text-sm">Atualização em {countdown}s</span>
              </div>
              <p className="text-xs text-blue-300">
                Última: {lastUpdate.toLocaleTimeString('pt-BR')}
              </p>
            </div>
          </div>
          
          {/* Navegação por Abas */}
          <nav className="flex gap-4 border-t border-white/10 pt-4">
            <a 
              href="/"
              className="px-4 py-2 rounded-lg bg-blue-500/20 border border-blue-400/50 text-white font-semibold hover:bg-blue-500/30 transition-all"
            >
              📊 Dashboard
            </a>
            <Link 
              href="/chat"
              className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-gray-300 hover:bg-white/10 hover:text-white transition-all"
            >
              🤖 Chatbot IA
            </Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Card: Gastos Parlamentares */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <DollarSign className="w-6 h-6 text-green-400" />
                Gastos
              </h2>
              <div className="bg-green-500/20 px-3 py-1 rounded-full">
                <span className="text-green-300 text-sm font-semibold">
                  {data?.gastos.totalRanking} deputados
                </span>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="bg-black/20 rounded-lg p-3">
                <p className="text-blue-300 text-sm mb-1">Progresso</p>
                <p className="text-white text-2xl font-bold">
                  {data?.gastos.ultimoProcessado} / {data?.gastos.totalRanking}
                </p>
                <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
                  <div 
                    className="bg-green-500 h-2 rounded-full transition-all"
                    style={{ 
                      width: `${((data?.gastos.ultimoProcessado || 0) / (data?.gastos.totalRanking || 1)) * 100}%` 
                    }}
                  />
                </div>
              </div>
              
              <div className="bg-black/20 rounded-lg p-3">
                <p className="text-blue-300 text-sm mb-2">Top Gastador</p>
                {data?.gastos.topGastadores[0] && (
                  <>
                    <p className="text-white font-semibold">
                      {data.gastos.topGastadores[0].nome}
                    </p>
                    <p className="text-sm text-gray-300">
                      {data.gastos.topGastadores[0].partido}-{data.gastos.topGastadores[0].uf}
                    </p>
                    <p className="text-green-400 text-xl font-bold mt-1">
                      {formatCurrency(data.gastos.topGastadores[0].totalGasto)}
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Card: Notícias */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Newspaper className="w-6 h-6 text-blue-400" />
                Notícias
              </h2>
              <div className="bg-blue-500/20 px-3 py-1 rounded-full">
                <span className="text-blue-300 text-sm font-semibold">
                  {data?.noticias.totalPostadas} postadas
                </span>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="bg-black/20 rounded-lg p-3">
                <p className="text-blue-300 text-sm mb-1">Total Publicadas</p>
                <p className="text-white text-3xl font-bold">
                  {data?.noticias.totalPostadas}
                </p>
              </div>
              
              {data?.noticias.ultimaNoticia && (
                <div className="bg-black/20 rounded-lg p-3">
                  <p className="text-blue-300 text-sm mb-2">Última Publicação</p>
                  <p className="text-xs text-gray-300 mb-2">
                    {formatDate(data.noticias.ultimaNoticia.posted_at)}
                  </p>
                  <a 
                    href={data.noticias.ultimaNoticia.link}
            target="_blank"
            rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 text-sm underline break-all"
                  >
                    Ver notícia →
                  </a>
                </div>
              )}
            </div>
          </div>

          {/* Card: Projetos de Lei */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 hover:bg-white/15 transition-all">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <FileText className="w-6 h-6 text-purple-400" />
                Projetos de Lei
              </h2>
              <div className="bg-purple-500/20 px-3 py-1 rounded-full">
                <span className="text-purple-300 text-sm font-semibold">
                  {data?.projetos.totalRastreados} PLs
                </span>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="bg-black/20 rounded-lg p-3">
                <p className="text-blue-300 text-sm mb-1">Rastreados</p>
                <p className="text-white text-3xl font-bold">
                  {data?.projetos.totalRastreados}
                </p>
              </div>
              
              {data?.projetos.ultimoProjeto && (
                <div className="bg-black/20 rounded-lg p-3">
                  <p className="text-blue-300 text-sm mb-2">Último Postado</p>
                  <p className="text-white font-semibold">
                    {data.projetos.ultimoProjeto.numero}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs bg-purple-500/30 text-purple-300 px-2 py-1 rounded">
                      {data.projetos.ultimoProjeto.categoria}
                    </span>
                    <span className="text-yellow-400">
                      {'⭐'.repeat(data.projetos.ultimoProjeto.importancia)}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tabela: Top 10 Gastadores */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
              <TrendingDown className="w-6 h-6 text-red-400" />
              Top 10 Maiores Gastadores
            </h2>
            <p className="text-sm text-blue-300 mt-2">
              💰 Valores acumulados dos últimos 3 meses • Fonte: Câmara dos Deputados
            </p>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/20">
                  <th className="text-left py-3 px-4 text-blue-300 font-semibold">#</th>
                  <th className="text-left py-3 px-4 text-blue-300 font-semibold">Deputado</th>
                  <th className="text-left py-3 px-4 text-blue-300 font-semibold">Partido</th>
                  <th className="text-left py-3 px-4 text-blue-300 font-semibold">UF</th>
                  <th className="text-right py-3 px-4 text-blue-300 font-semibold">Gasto Total</th>
                </tr>
              </thead>
              <tbody>
                {data?.gastos.topGastadores.map((deputado, index) => (
                  <tr 
                    key={index}
                    className="border-b border-white/10 hover:bg-white/5 transition-colors"
                  >
                    <td className="py-3 px-4 text-white font-bold">
                      {index + 1}
                    </td>
                    <td className="py-3 px-4 text-white">
                      {deputado.nome}
                    </td>
                    <td className="py-3 px-4 text-gray-300">
                      {deputado.partido}
                    </td>
                    <td className="py-3 px-4 text-gray-300">
                      {deputado.uf}
                    </td>
                    <td className="py-3 px-4 text-right text-green-400 font-semibold">
                      {formatCurrency(deputado.totalGasto)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Grid de Notícias e PLs */}
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Coluna 1: Notícias Recentes */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <Newspaper className="w-6 h-6 text-blue-400" />
              Notícias Recentes
            </h2>
            
            {data?.noticias.recentes && data.noticias.recentes.length > 0 ? (
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {data.noticias.recentes.slice(0, 10).map((noticia, index) => {
                  const url = new URL(noticia.link);
                  const fonte = url.hostname.includes('senado') ? '🏛️ Senado' :
                               url.hostname.includes('camara') ? '🏛️ Câmara' :
                               url.hostname.includes('stf') ? '⚖️ STF' :
                               url.hostname.includes('tse') ? '🗳️ TSE' :
                               url.hostname.includes('agenciabrasil') ? '📰 Agência Brasil' : '📰 Notícia';
                  
                  return (
                    <div 
                      key={index}
                      className="bg-black/20 rounded-lg p-4 hover:bg-black/30 transition-all"
                    >
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <span className="text-xs bg-blue-500/30 text-blue-300 px-2 py-1 rounded">
                          {fonte}
                        </span>
                        <span className="text-xs text-gray-400">
                          {formatDate(noticia.posted_at)}
                        </span>
                      </div>
                      <a 
                        href={noticia.link}
            target="_blank"
            rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 text-sm underline break-all line-clamp-2"
                      >
                        {noticia.link.split('/').pop()?.replace(/-/g, ' ')}
                      </a>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">
                Nenhuma notícia postada ainda
              </p>
            )}
          </div>

          {/* Coluna 2: Projetos de Lei */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <FileText className="w-6 h-6 text-purple-400" />
              Projetos de Lei Rastreados
            </h2>
            
            {data?.projetos.recentes && data.projetos.recentes.length > 0 ? (
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {data.projetos.recentes.map((projeto, index) => {
                  const emojiCategoria: Record<string, string> = {
                    'economia': '💰',
                    'saúde': '🏥',
                    'educação': '📚',
                    'segurança': '👮',
                    'trabalho': '👷',
                    'meio ambiente': '🌳',
                    'diversos': '📋'
                  };
                  
                  return (
                    <div 
                      key={index}
                      className="bg-black/20 rounded-lg p-4 hover:bg-black/30 transition-all"
                    >
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <span className="text-white font-bold text-lg">
                          {projeto.numero}
                        </span>
                        {projeto.posted && (
                          <span className="text-xs bg-green-500/30 text-green-300 px-2 py-1 rounded">
                            ✓ Postado
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-xs bg-purple-500/30 text-purple-300 px-2 py-1 rounded flex items-center gap-1">
                          {emojiCategoria[projeto.categoria] || '📋'}
                          {projeto.categoria}
                        </span>
                        <span className="text-yellow-400 text-sm">
                          {'⭐'.repeat(projeto.importancia)}
                        </span>
                      </div>
                      
                      {/* Ementa (Resumo) */}
                      <p className="text-sm text-white mb-3 leading-relaxed">
                        {projeto.ementa}
                      </p>
                      
                      <div className="border-t border-white/10 pt-2 mt-2">
                        <p className="text-xs text-gray-400 mb-1">
                          📋 Status: {projeto.last_status}
                        </p>
                        <p className="text-xs text-gray-400">
                          🗓️ Rastreado em: {formatDate(projeto.tracked_at)}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">
                Nenhum projeto rastreado ainda
              </p>
            )}
          </div>
        </div>

        {/* Categorias de PLs */}
        {data?.projetos.porCategoria && Object.keys(data.projetos.porCategoria).length > 0 && (
          <div className="mt-6 bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
            <h2 className="text-2xl font-bold text-white mb-6">
              📊 Projetos por Categoria
            </h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(data.projetos.porCategoria).map(([categoria, count]) => (
                <div key={categoria} className="bg-black/20 rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-white mb-1">{count}</p>
                  <p className="text-sm text-blue-300 capitalize">{categoria}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Grid: Votações e Medidas Provisórias */}
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Coluna 1: Votações Recentes */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              🗳️ Votações Recentes
            </h2>
            
            {(() => {
              // Filtra votações que têm votos computados
              const votacoesComVotos = data?.votacoes.recentes?.filter(v => 
                (v.votos_sim > 0 || v.votos_nao > 0 || v.votos_outros > 0)
              ) || [];
              
              return votacoesComVotos.length > 0 ? (
                <div className="space-y-4">
                  {votacoesComVotos.map((votacao, index) => {
                    const resultado = votacao.aprovacao === true ? 'APROVADO' : 
                                    votacao.aprovacao === false ? 'REJEITADO' : 'N/A';
                    const corResultado = votacao.aprovacao === true ? 'text-green-400' : 
                                        votacao.aprovacao === false ? 'text-red-400' : 'text-gray-400';
                    
                    return (
                      <div 
                        key={index}
                        className="bg-black/20 rounded-lg p-4 hover:bg-black/30 transition-all"
                      >
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <span className={`text-sm font-bold ${corResultado}`}>
                            {resultado}
                          </span>
                          <span className="text-yellow-400">
                            {'⭐'.repeat(votacao.importancia)}
                          </span>
                        </div>
                        
                        <p className="text-sm text-white mb-3">
                          {votacao.descricao || votacao.proposicao}
                        </p>
                        
                        <div className="grid grid-cols-3 gap-2 text-center">
                          <div className="bg-green-500/20 rounded py-2">
                            <p className="text-lg font-bold text-green-300">{votacao.votos_sim}</p>
                            <p className="text-xs text-green-300">SIM</p>
                          </div>
                          <div className="bg-red-500/20 rounded py-2">
                            <p className="text-lg font-bold text-red-300">{votacao.votos_nao}</p>
                            <p className="text-xs text-red-300">NÃO</p>
                          </div>
                          <div className="bg-gray-500/20 rounded py-2">
                            <p className="text-lg font-bold text-gray-300">{votacao.votos_outros}</p>
                            <p className="text-xs text-gray-300">OUTROS</p>
                          </div>
                        </div>
                        
                        <p className="text-xs text-gray-400 mt-2">
                          {formatDate(votacao.data)}
                        </p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-8">
                  Nenhuma votação com votos computados
                </p>
              );
            })()}
          </div>

          {/* Coluna 2: Medidas Provisórias */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              ⚡ Medidas Provisórias
            </h2>
            
            {data?.medidas_provisorias.recentes && data.medidas_provisorias.recentes.length > 0 ? (
              <div className="space-y-4">
                {data.medidas_provisorias.recentes.map((mp, index) => {
                  const urgenciaCor = mp.prazo_vencido ? 'bg-red-500/30 text-red-300' :
                                     mp.nivel_urgencia >= 4 ? 'bg-orange-500/30 text-orange-300' :
                                     mp.nivel_urgencia >= 3 ? 'bg-yellow-500/30 text-yellow-300' :
                                     'bg-green-500/30 text-green-300';
                  
                  return (
                    <div 
                      key={index}
                      className="bg-black/20 rounded-lg p-4 hover:bg-black/30 transition-all"
                    >
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <span className="text-white font-bold">{mp.numero}</span>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-1 rounded ${urgenciaCor}`}>
                            {mp.prazo_vencido ? '⚠️ VENCIDA' : `${mp.dias_restantes}d`}
                          </span>
                          <span className="text-yellow-400">
                            {'⭐'.repeat(mp.importancia)}
                          </span>
                        </div>
                      </div>
                      
                      <p className="text-sm text-white mb-3 leading-relaxed">
                        {mp.ementa.substring(0, 120)}...
                      </p>
                      
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs bg-purple-500/30 text-purple-300 px-2 py-1 rounded">
                          {mp.categoria}
                        </span>
                        <span className="text-xs text-gray-400">
                          {mp.status}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">
                Nenhuma MP ativa no momento
              </p>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-black/30 backdrop-blur-lg border-t border-white/10 mt-12">
        <div className="container mx-auto px-6 py-6 text-center">
          <p className="text-blue-300">
            Dados atualizados automaticamente a cada 30 segundos
          </p>
          <p className="text-sm text-gray-400 mt-2">
            Monitor PL Brasil • Transparência Legislativa em Tempo Real
          </p>
        </div>
      </footer>
    </div>
  );
}
