import { NextRequest, NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';
import { rateLimit } from '../../../lib/rateLimit';

export async function GET(request: NextRequest) {
  // Rate limiting: 60 requests por minuto
  const rateLimitResponse = await rateLimit(request, 60);
  if (rateLimitResponse) {
    return rateLimitResponse;
  }

  try {
    // Caminhos para os arquivos JSON (um nível acima da pasta dashboard)
    const basePath = join(process.cwd(), '..');
    
    // Ler estado.json
    const estadoPath = join(basePath, 'estado.json');
    const estadoData = await readFile(estadoPath, 'utf-8');
    const estado = JSON.parse(estadoData);
    
    // Ler ranking_gastos.json
    const rankingPath = join(basePath, 'ranking_gastos.json');
    const rankingData = await readFile(rankingPath, 'utf-8');
    const ranking = JSON.parse(rankingData);
    
    // Processar dados de gastos
    const gastosData = {
      ultimoProcessado: estado.last_processed_deputy_index || 0,
      totalRanking: ranking.length,
      topGastadores: ranking.slice(0, 10).map((deputado: any) => ({
        nome: deputado.nome,
        partido: deputado.siglaPartido,
        uf: deputado.siglaUf,
        totalGasto: deputado.total_gasto
      }))
    };
    
    // Processar dados de notícias
    const noticiasData = {
      totalPostadas: estado.posted_news?.length || 0,
      ultimaNoticia: estado.posted_news && estado.posted_news.length > 0
        ? estado.posted_news[estado.posted_news.length - 1]
        : null,
      recentes: estado.posted_news ? [...estado.posted_news].reverse().slice(0, 15) : []
    };
    
    // Processar dados de projetos de lei
    const trackedProjects = estado.tracked_projects || [];
    const porCategoria: Record<string, number> = {};
    
    trackedProjects.forEach((project: any) => {
      const cat = project.categoria || 'diversos';
      porCategoria[cat] = (porCategoria[cat] || 0) + 1;
    });
    
    const projetosData = {
      totalRastreados: trackedProjects.length,
      porCategoria,
      ultimoProjeto: trackedProjects.length > 0
        ? {
            numero: trackedProjects[trackedProjects.length - 1].numero,
            categoria: trackedProjects[trackedProjects.length - 1].categoria,
            importancia: trackedProjects[trackedProjects.length - 1].importancia
          }
        : null,
      recentes: [...trackedProjects].reverse().slice(0, 15)
    };
    
    // Processar dados de votações
    const recentVotes = estado.recent_votes || [];
    const votacoesData = {
      totalVotacoes: recentVotes.length,
      recentes: recentVotes.slice(0, 10)
    };
    
    // Processar dados de Medidas Provisórias
    const activeMps = estado.active_mps || [];
    const mpsData = {
      totalAtivas: activeMps.length,
      recentes: activeMps.slice(0, 10)
    };
    
    // Montar resposta final
    const dashboardData = {
      gastos: gastosData,
      noticias: noticiasData,
      projetos: projetosData,
      votacoes: votacoesData,
      medidas_provisorias: mpsData,
      ultimaAtualizacao: new Date().toISOString()
    };
    
    return NextResponse.json(dashboardData);
    
  } catch (error: any) {
    console.error('Erro ao ler dados:', error);
    return NextResponse.json(
      { 
        error: 'Erro ao carregar dados',
        message: error.message 
      },
      { status: 500 }
    );
  }
}

// Revalidar a cada 10 segundos
export const revalidate = 10;

