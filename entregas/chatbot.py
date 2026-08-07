"""
chatbot.py — ChargeGrid Intelligence Assistant, versão local (sem Colab)
GoodWe Challenge - Sprint 3

Mesma lógica do ChargeGrid_Intelligence_chatbot.ipynb (roteador tempo real
vs. histórico, RAG com dados_rag.json, IA via Groq) — só que rodando direto
no seu computador, num terminal, sem precisar de Colab nem upload de nada.
Reaproveita o mesmo .env que a API já usa (DATABASE_URL, GROQ_API_KEY).

Como rodar:
  cd entregas
  py chatbot.py
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

from ev_chargegrid import (
    listar_sessoes_ativas,
    obter_status_estacoes,
    obter_faturamento_dia,
    contar_sessoes_dia,
    inicializar_banco,
)

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

inicializar_banco()  # garante que o banco existe antes de qualquer leitura

PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(PASTA_ATUAL, "dados_rag.json"), "r", encoding="utf-8") as f:
    dados_rag = json.load(f)

documentos = dados_rag["frases_contexto_rag"]

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODELO = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """
[1] IDENTIDADE:
Você é o assistente inteligente do Charge Grid Intelligence, um sistema de gestão de
eletropostos para operações comerciais no contexto do EV Challenge 2026.

[2] CONTEXTO:
O Charge Grid Intelligence é um sistema voltado para postos comerciais e operadores
de frotas que precisam gerenciar eletropostos de alto fluxo de forma eficiente.
Você ajuda de duas formas: (a) consultando dados reais do sistema — sessões de
recarga, receita por ponto de carga, disponibilidade dos carregadores — e (b)
funcionando como um guia de bolso pro motorista, tirando dúvidas gerais sobre
carros elétricos (autonomia, tipos de conector, cuidados com a bateria, como
funciona a recarga).
A partir do Sprint 3, o chatbot tem acesso a dois tipos de dados sobre o sistema:
- DADOS EM TEMPO REAL: estado atual do sistema (carregadores ativos, faturamento de hoje)
- DADOS HISTÓRICOS: análise de 60 sessões reais da base SP2 (receita por carregador,
  pico de demanda, ticket médio, eficiência do DLB)

[3] REGRAS:
- Responda sobre o sistema Charge Grid Intelligence, operação de eletropostos, e
  dúvidas gerais de motoristas sobre carros elétricos.
- Se a pergunta não tiver relação nenhuma com recarga, carros elétricos ou o
  sistema, diga: "Só consigo ajudar com questões relacionadas a carros
  elétricos e ao Charge Grid Intelligence."
- Nunca invente dados do sistema (valores de consumo, faturamento) nem
  especificações técnicas exatas de um modelo específico de carro — se não
  tiver certeza sobre um modelo específico, diga isso claramente em vez de
  arriscar um número.
- Não opine sobre qual marca de carro ou rede de recarga é "melhor" — explique
  conceitos, não compare produtos.
- "Gasto pessoal do motorista logado" e "faturamento/receita total do sistema"
  são coisas DIFERENTES — nunca confunda os dois. Gasto pessoal é o que aquele
  motorista específico pagou; faturamento total é dado de negócio, somando
  todos os clientes. Se a pergunta for "quanto eu gastei" ou parecida, use
  APENAS o dado de "gasto pessoal do motorista logado" quando ele estiver no
  contexto — nunca responda com o faturamento total do sistema nesse caso.
- Quando tiver dados em tempo real disponíveis no contexto, priorize-os sobre o histórico.

[4] TOM DE VOZ:
Seja claro, objetivo e use linguagem acessível, sem jargões técnicos
desnecessários. Responda sempre em português brasileiro.

[5] CONTEXTO DO SISTEMA:
- O sistema atende postos comerciais e frotas com múltiplos pontos de carga e alta rotatividade
- A cobrança é feita por kWh consumido com tarifa dinâmica por horário e ocupação
- O chatbot orienta gestores e operadores sobre consumo, faturamento e disponibilidade do sistema
- Picos de demanda são previstos e tarifados para evitar sobrecarga na infraestrutura elétrica
"""

PALAVRAS_TEMPO_REAL = [
    "agora", "hoje", "atual", "ativo", "ativa", "livre", "ocupado", "ocupada",
    "faturamento", "sessões de hoje", "quantas sessões", "status",
    "disponível", "carregando"
]


def buscar_contexto(pergunta: str) -> str:
    pergunta_lower = pergunta.lower()
    usa_tempo_real = any(p in pergunta_lower for p in PALAVRAS_TEMPO_REAL)

    partes = []

    if usa_tempo_real:
        try:
            sessoes_ativas = listar_sessoes_ativas()
            status_estacoes = obter_status_estacoes()
            faturamento_hoje = obter_faturamento_dia()
            sessoes_hoje = contar_sessoes_dia()

            livres = [k for k, v in status_estacoes.items() if v == "Livre"]
            ocupadas = [k for k, v in status_estacoes.items() if v == "Ocupada"]

            partes.append("[DADOS EM TEMPO REAL — banco Postgres]")
            partes.append(f"Estações ocupadas agora: {ocupadas if ocupadas else 'nenhuma'}")
            partes.append(f"Estações livres agora: {livres}")
            partes.append(f"Faturamento de hoje (sessões pagas): R$ {faturamento_hoje:.2f}")
            partes.append(f"Total de sessões iniciadas hoje: {sessoes_hoje}")

            for s in sessoes_ativas:
                partes.append(
                    f"Sessão ativa — Estação {s['estacao']}: usuário {s['usuario']}, "
                    f"{s['kwh']:.2f} kWh consumidos, valor acumulado R$ {s['valor']:.2f}, "
                    f"pagamento via {s['pagamento']}."
                )
        except Exception as e:
            partes.append(f"[AVISO] Banco indisponível: {e}")
    else:
        palavras = pergunta_lower.split()
        relevantes = [doc for doc in documentos if any(p in doc.lower() for p in palavras)]
        if relevantes:
            partes.append("[DADOS HISTÓRICOS — planilha SP2, 60 sessões reais]")
            partes.extend(relevantes[:5])

    return "\n".join(partes)


historico = [{"role": "system", "content": SYSTEM_PROMPT}]


def chat(pergunta: str) -> str:
    contexto = buscar_contexto(pergunta)
    if contexto:
        mensagem = f"Contexto do sistema:\n{contexto}\n\nPergunta: {pergunta}"
    else:
        mensagem = pergunta
    historico.append({"role": "user", "content": mensagem})
    resposta = client.chat.completions.create(model=MODELO, messages=historico)
    conteudo = resposta.choices[0].message.content
    historico.append({"role": "assistant", "content": conteudo})
    return conteudo


def responder(pergunta: str, contexto_extra: str = None) -> str:
    """Versão sem estado (não usa/altera o `historico` global) — cada
    chamada é independente. Usada pela API (/api/chat), que pode atender
    vários usuários ao mesmo tempo e não deve misturar a conversa de um
    com a de outro.

    contexto_extra: dado do motorista logado (gasto pessoal), montado pela
    API — só depois de validar o PIN dele. Este arquivo não sabe nada sobre
    placas/PIN/autenticação, só monta a pergunta com o que a API já mandou
    pronto e verificado."""
    contexto = buscar_contexto(pergunta)
    if contexto_extra:
        contexto = f"{contexto_extra}\n{contexto}" if contexto else contexto_extra
    mensagem = f"Contexto do sistema:\n{contexto}\n\nPergunta: {pergunta}" if contexto else pergunta
    resposta = client.chat.completions.create(
        model=MODELO,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": mensagem},
        ],
    )
    return resposta.choices[0].message.content


def main() -> None:
    print("ChargeGrid Intelligence — CGI Assistant (local)")
    print(f"RAG com {len(documentos)} fragmentos históricos indexados.")
    print("Digite 'sair' para encerrar.\n")

    while True:
        pergunta = input("Você: ").strip()
        if not pergunta:
            continue
        if pergunta.lower() in ("sair", "exit", "quit"):
            print("\nAté mais!")
            break
        print("Bot:", chat(pergunta), "\n")


if __name__ == "__main__":
    main()
