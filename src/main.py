"""Módulo principal para o Monitor PL Brasil."""
import json
from collections import defaultdict
from dotenv import load_dotenv

from src.api_client import get_deputy_expenses, post_tweet

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

STATE_FILE = 'estado.json'
RANKING_FILE = 'ranking_gastos.json'


def load_json(file_path):
    """Carrega um arquivo JSON."""
    try:
        with open(file_path, 'r', encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def save_json(data, file_path):
    """Salva dados em um arquivo JSON."""
    with open(file_path, 'w', encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def process_expenses(expenses):
    """
    Processa uma lista de despesas para calcular o total gasto,
    agrupar despesas por categoria e identificar a maior despesa única.
    """
    if not expenses:
        return 0, {}, None

    total_spent = 0
    grouped_expenses = defaultdict(float)
    largest_single_expense = {"valorLiquido": 0}

    for expense in expenses:
        total_spent += expense['valorLiquido']
        category_name = expense['tipoDespesa'].replace(".", "").strip().title()
        grouped_expenses[category_name] += expense['valorLiquido']

        if expense['valorLiquido'] > largest_single_expense['valorLiquido']:
            largest_single_expense = expense

    sorted_grouped_expenses = sorted(grouped_expenses.items(),
                                     key=lambda item: item[1],
                                     reverse=True)
    return total_spent, dict(sorted_grouped_expenses), largest_single_expense


def generate_thread_content(deputy_id, deputy_name, deputy_party,
                            total_spent, grouped_expenses, largest_expense):
    """
    Gera o conteúdo da thread para postagem no X (Twitter)
    com base nos dados de gastos do deputado.
    """
    tweet1 = (f"📊 Gastos Parlamentares: R$ {total_spent:,.2f}\n\n"
              f"Deputado(a): {deputy_name} ({deputy_party}) utilizou este valor "
              "da cota parlamentar nos últimos 3 meses.\n\n"
              "👇 Siga o fio para ver os detalhes e as fontes.\n\n"
              "#MonitorPL #TransparenciaBrasil #Fiscalize #Governo #GastosPúblicos")

    tweet2 = "🧵 Detalhes dos Gastos:\n\n"
    emoji_map = {
        "Divulgação Da Atividade Parlamentar": "📢",
        "Combustíveis E Lubrificantes": "⛽",
        "Passagem Aérea - Sigepa": "✈️",
        "Manutenção De Escritório De Apoio À Atividade Parlamentar": "🏢",
        "Locação Ou Fretamento De Veículos Automotores": "🚗",
        "Telefonia": "📱",
        "Serviços Postais": "✉️"
    }
    count = 0
    for category, value in grouped_expenses.items():
        if count < 5:
            emoji = emoji_map.get(category, "▪️")
            line = f"{emoji} {category}: R$ {value:,.2f}\n"
            if len(tweet2) + len(line) < 280:
                tweet2 += line
                count += 1

    tweet3 = ""
    if largest_expense and largest_expense['valorLiquido'] > 0:
        valor = largest_expense['valorLiquido']
        fornecedor = largest_expense['nomeFornecedor'].title()
        tweet3 += (f"✨ Destaque: O maior gasto único foi de R$ {valor:,.2f} "
                   f"com \"{fornecedor}\".\n\n")

    tweet3 += (f"📊 Acompanhe os gastos completos em:\n"
               f"https://www.camara.leg.br/deputados/{deputy_id}\n\n"
               "#DadosAbertos")

    return [tweet1, tweet2, tweet3]


def main():
    """Função principal que executa o bot."""
    print("Iniciando bot de gastos parlamentares...")

    # Carregar estado
    state = load_json(STATE_FILE)
    if state is None:
        state = {"last_processed_deputy_index": 0}

    # Carregar ranking
    ranking = load_json(RANKING_FILE)
    if not ranking:
        print("Erro: Arquivo de ranking não encontrado. Execute gerador_de_ranking.py primeiro.")
        return

    # Pegar próximo deputado
    index = state["last_processed_deputy_index"]
    if index >= len(ranking):
        print("Todos os deputados já foram processados. Reiniciando do início.")
        index = 0

    deputy = ranking[index]
    deputy_id = deputy['id']
    deputy_name = deputy['nome']
    deputy_party = deputy['siglaPartido']

    print(f"Processando: {deputy_name} ({deputy_party})")

    # Buscar despesas
    expenses = get_deputy_expenses(deputy_id)
    total_spent, grouped_expenses, largest_expense = process_expenses(expenses)

    if total_spent == 0:
        print(f"Deputado {deputy_name} não tem gastos registrados. Pulando.")
        state["last_processed_deputy_index"] = index + 1
        save_json(state, STATE_FILE)
        return

    # Gerar e postar thread
    thread = generate_thread_content(deputy_id, deputy_name, deputy_party,
                                     total_spent, grouped_expenses, largest_expense)

    print("Postando thread...")
    last_tweet_id = None
    for tweet in thread:
        result = post_tweet(tweet, reply_to_id=last_tweet_id)
        if result == "duplicate":
            print("Tweet duplicado detectado. Continuando...")
            break
        if not result:
            print("Erro ao postar tweet. Abortando.")
            return
        last_tweet_id = result

    # Atualizar estado
    state["last_processed_deputy_index"] = index + 1
    save_json(state, STATE_FILE)
    print(f"Thread postada com sucesso! Próximo índice: {index + 1}")


if __name__ == "__main__":
    main()
