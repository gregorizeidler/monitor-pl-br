import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';

// Configuração do OpenAI
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

// Configuração do banco de dados
const DATABASE_PATH = path.join(process.cwd(), '..', 'database', 'monitor_pl.db');

// Interface para mensagens
interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

// Função para abrir conexão com o banco
async function getDB() {
  return open({
    filename: DATABASE_PATH,
    driver: sqlite3.Database
  });
}

// Função para executar queries SQL
async function executeQuery(query: string): Promise<any[]> {
  try {
    const db = await getDB();
    const result = await db.all(query);
    await db.close();
    return result;
  } catch (error) {
    console.error('Erro ao executar query:', error);
    return [];
  }
}

// Função que a IA pode chamar para buscar dados
async function queryDatabase(sqlQuery: string): Promise<string> {
  console.log('🔍 Executando query:', sqlQuery);
  
  try {
    const results = await executeQuery(sqlQuery);
    
    if (results.length === 0) {
      return 'Nenhum resultado encontrado para esta consulta.';
    }
    
    // Formatar resultados em JSON legível
    return JSON.stringify(results, null, 2);
  } catch (error) {
    return `Erro ao executar query: ${error}`;
  }
}

// System prompt que explica o contexto ao ChatGPT
const SYSTEM_PROMPT = `Você é um assistente especializado em dados parlamentares brasileiros.

BANCO DE DADOS DISPONÍVEL:
Você tem acesso a um banco SQLite com as seguintes tabelas:

1. **deputados** - Informações sobre deputados
   - id, nome, partido, uf, url_foto, email, etc

2. **gastos** - Gastos parlamentares (cota CEAP)
   - id, deputado_id, mes, ano, tipo_despesa, data_documento, valor_documento, valor_liquido, fornecedor

3. **projetos_lei** - Projetos de Lei
   - id, numero, ano, tipo, ementa, data_apresentacao, importancia, categoria

4. **votacoes** - Votações na Câmara
   - id, data_hora_registro, descricao, aprovacao, votos_sim, votos_nao, votos_outros

5. **medidas_provisorias** - Medidas Provisórias
   - id, numero, ementa, data_apresentacao, status, dias_restantes, nivel_urgencia

6. **votos_deputados** - Votos individuais de cada deputado
   - id, votacao_id, deputado_id, tipo_voto

VIEWS DISPONÍVEIS:
- vw_estatisticas_gerais - Estatísticas gerais do banco
- vw_pls_por_categoria_ano - PLs agrupados por categoria e ano
- vw_ranking_gastos_12m - Ranking de gastos dos últimos 12 meses
- vw_taxa_aprovacao_votacoes - Taxa de aprovação de votações por ano

INSTRUÇÕES:
1. Quando o usuário fizer uma pergunta, analise o que ele quer saber
2. Use a função queryDatabase para buscar os dados necessários
3. Sempre formate os valores monetários como R$ X.XXX,XX
4. Seja objetivo e direto nas respostas
5. Se não tiver certeza da query, explique sua lógica
6. Forneça contexto e insights sobre os dados

EXEMPLOS DE QUERIES:
- "SELECT d.nome, SUM(g.valor_liquido) as total FROM deputados d JOIN gastos g ON d.id = g.deputado_id GROUP BY d.id ORDER BY total DESC LIMIT 10"
- "SELECT categoria, COUNT(*) as total FROM projetos_lei GROUP BY categoria ORDER BY total DESC"
- "SELECT * FROM vw_estatisticas_gerais"

Responda em português brasileiro de forma natural e conversacional.`;

// Handler da API
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { messages } = body;

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json(
        { error: 'Messages inválidas' },
        { status: 400 }
      );
    }

    // Adicionar system prompt
    const messagesWithSystem = [
      { role: 'system', content: SYSTEM_PROMPT },
      ...messages
    ];

    console.log('💬 Recebido:', messages[messages.length - 1]?.content);

    // Chamar OpenAI com Function Calling
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: messagesWithSystem as any,
      functions: [
        {
          name: 'queryDatabase',
          description: 'Executa uma query SQL no banco de dados de dados parlamentares. Use esta função para buscar informações sobre gastos, deputados, projetos de lei, votações, etc.',
          parameters: {
            type: 'object',
            properties: {
              sqlQuery: {
                type: 'string',
                description: 'A query SQL a ser executada. Deve ser uma query SELECT válida.'
              }
            },
            required: ['sqlQuery']
          }
        }
      ],
      function_call: 'auto',
      temperature: 0.7,
      max_tokens: 1000
    });

    let responseMessage = completion.choices[0].message;

    // Se a IA chamou uma função, executar e pedir resposta final
    if (responseMessage.function_call) {
      const functionName = responseMessage.function_call.name;
      const functionArgs = JSON.parse(responseMessage.function_call.arguments);

      console.log('🤖 IA chamou função:', functionName, 'com args:', functionArgs);

      let functionResponse = '';

      if (functionName === 'queryDatabase') {
        functionResponse = await queryDatabase(functionArgs.sqlQuery);
      }

      console.log('📊 Resultado da query:', functionResponse.substring(0, 200) + '...');

      // Pedir para a IA formatar a resposta final
      const secondCompletion = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [
          ...messagesWithSystem as any,
          responseMessage as any,
          {
            role: 'function',
            name: functionName,
            content: functionResponse
          }
        ],
        temperature: 0.7,
        max_tokens: 1500
      });

      responseMessage = secondCompletion.choices[0].message;
    }

    console.log('✅ Resposta final:', responseMessage.content?.substring(0, 100) + '...');

    return NextResponse.json({
      message: responseMessage.content || 'Desculpe, não consegui processar sua pergunta.',
      timestamp: new Date().toISOString()
    });

  } catch (error: any) {
    console.error('❌ Erro na API:', error);
    
    return NextResponse.json(
      { 
        error: 'Erro ao processar mensagem',
        details: error.message 
      },
      { status: 500 }
    );
  }
}
