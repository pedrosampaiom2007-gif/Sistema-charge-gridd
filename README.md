# ChargeGrid Intelligence

<p align="center">
<img src="./assets/goodwe.png" width="95%">
</p>

Sistema de gestão comercial de recarga de veículos elétricos, desenvolvido para o EV Challenge 2026 (GoodWe / FIAP). Cobre o ciclo completo de uma sessão de recarga comercial: autoatendimento no totem, cobrança via Pix simulado, painel operacional para o gestor (com login), uma área pessoal do motorista (histórico de pagamentos, suporte a mais de um carro por conta) e um assistente conversacional que responde tanto sobre o sistema quanto dúvidas gerais de carro elétrico.

<br>

## Visão geral

O motor (`entregas/ev_chargegrid.py`) controla até 10 estações de recarga: autenticação de motorista por placa (hash SHA-256, com mascaramento em conformidade com a LGPD), balanceamento de carga entre estações ativas (DLB), tarifação dinâmica por horário e demanda, e pagamento via gateway simulado (Mercado Pago sandbox). Uma API Flask expõe esse motor para três clientes web (totem, dashboard, app do motorista) e um chatbot (rodando local ou no Colab) que responde em linguagem natural, combinando dados em tempo real com um histórico de 60 sessões reais.

**O banco de dados é Postgres na nuvem (Supabase), não um arquivo local** — qualquer processo, de qualquer computador com a credencial certa, lê e escreve no mesmo banco. **A IA do chatbot roda na nuvem (Groq)**, não localmente — não depende de instalar nem baixar modelo nenhum.

<br>

## 📚 Documentação

| Documento | Conteúdo |
|---|---|
| ⚙️ [`docs/INSTALL.md`](docs/INSTALL.md) | Configuração do `.env` e passo a passo completo pra rodar e testar o projeto do zero |
| 🏗️ [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Diagrama de arquitetura, estrutura do repositório e fluxo principal |
| 🔒 [`docs/SECURITY.md`](docs/SECURITY.md) | Revisão de segurança (rate limiting, CORS, IDOR, etc.) e limitações conhecidas |
| 📝 [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | O que já foi resolvido, auditoria completa dos módulos e novidades recentes |
| 🚀 [`docs/DEPLOY.md`](docs/DEPLOY.md) | Como publicar a API em produção (Render/Railway) |
| 💼 [`docs/BUSINESS_MODEL.md`](docs/BUSINESS_MODEL.md) | Modelo de negócio e comissão |

<br>

## Início rápido

```powershell
cd entregas
pip install -r "requirements (1).txt"
cd files
python api_server.py
```

Depois é só abrir `entregas/index.html` no navegador. Passo a passo completo, com configuração do `.env` e testes, em [`docs/INSTALL.md`](docs/INSTALL.md).

<br>

## Equipe

Pedro Sampaio, Raul Sampaio, Lucas Garcia, Luan de Araujo, Kevin Rodrigues, Pedro Ribeiro Lopes — EV Challenge 2026, GoodWe / FIAP.
