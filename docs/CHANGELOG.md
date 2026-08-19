# 📝 Changelog — O que já foi resolvido

## O que já foi resolvido

- Motor completo: banco Postgres (Supabase), autenticação com hash, mascaramento LGPD, pagamento sandbox, balanceamento de carga.
- **Contas com mais de um carro**: uma conta pode ter várias placas vinculadas; login com qualquer uma delas mostra o histórico combinado.
- Modelo de IA preditiva treinado com dados reais e integrado ao motor.
- API Flask cobrindo sessões, painel, KPIs, curva de demanda, login admin, histórico de pagamentos, vínculo de carro e chat.
- **Login de administrador** de verdade (usuário/senha, token), protegendo todo dado agregado de negócio (`/api/kpis`, `/api/demanda-ia`, `/api/tempo/avancar` e o modo de gestão do chat). O `/api/painel` continua aberto porque o totem também precisa dele — mas só com estado de estação, sem número de faturamento.
- Totem, dashboard e app do motorista funcionais, testados ponta a ponta com dados reais passando pelo sistema.
- Chatbot com roteador de tempo real (banco) vs. histórico (RAG) vs. dúvidas gerais de carro elétrico, rodando com Groq (nuvem, sem custo no uso normal) — disponível como script local ou notebook Colab, sem exigir upload manual de arquivo em nenhum dos dois.
- Recuperação automática de sessões ativas quando a API reinicia (evita duplicar sessão na mesma estação).
- Landing page única, separando claramente os três públicos (motorista no totem, motorista no app, administrador).
- **Testes automatizados** (`entregas/tests/`) cobrindo tarifação dinâmica, DLB, hash/mascaramento LGPD e a correção da demo comercial — ver `docs/INSTALL.md`, passo 11.
- Modelo de IA preditiva (`modelo_demanda.pkl`) agora carrega de verdade também rodando pelo fluxo documentado (`cd entregas/files && python api_server.py`) — o carregamento usava caminho relativo e dependia do diretório de onde o processo era iniciado; sem isso, a API sempre caía no dicionário de tarifas fixo, mesmo com o modelo treinado disponível.
- API pronta pra deploy: porta e modo debug configuráveis por variável de ambiente (`PORT`, `FLASK_DEBUG`) e `Procfile`/`render.yaml` no repositório — ver `docs/DEPLOY.md`.
- **Revisão de segurança** (ver `docs/SECURITY.md`): rate limiting, CORS por allowlist, cabeçalhos anti-clickjacking, bloqueio de conta por tentativas de login e revogação de token no logout.
- **Cadastro de novo motorista**: antes, uma placa não reconhecida travava sem nenhum caminho pra frente — o sistema só funcionava pras 4 placas de teste. Agora dá pra se cadastrar direto no totem (quando a placa não é reconhecida na hora de iniciar a recarga) ou no app (link "Ainda não tem cadastro?" na tela de login) — os dois usam o mesmo `POST /api/usuarios`.
- **PIN de 4 dígitos** (escolhido no cadastro) protegendo o histórico de pagamento — ver "IDOR corrigido" em `docs/SECURITY.md`.
- **Chat sem vazar dado de negócio pro motorista**: o assistente, quando usado de dentro da conta do motorista (placa+PIN), não revela faturamento, receita histórica nem qualquer número agregado do sistema — só o gasto pessoal daquele motorista, disponibilidade de estação, e dúvidas gerais de carro elétrico. Achado testando com um usuário real fora da equipe — ver `docs/SECURITY.md`.
- **Manutenção de estação, tarifa de madrugada e relatório do dia pra download** — ver "Novidades" abaixo pra detalhe técnico, e [`docs/BUSINESS_MODEL.md`](BUSINESS_MODEL.md) pro modelo de negócio.

<br>

## Revisão profunda (auditoria de todos os módulos)

Varredura completa de motor, API, chatbot e as três telas, com cada achado reproduzido antes de corrigir e reverificado depois, contra o Supabase de verdade. O que estava quebrado:

- **Chat liberava o negócio inteiro pra quem NÃO se identificava**: a restrição de dado de negócio só ligava quando o motorista mandava placa+PIN. Chamar `/api/chat` sem nada — que qualquer pessoa com a URL da API pode fazer — devolvia faturamento do dia, contagem de sessões, as sessões ativas dos outros clientes e todo o histórico comercial. Quem se identificava via menos que um anônimo. Agora o padrão é o mais restrito, e o acesso de gestão exige token de admin, igual ao `/api/kpis`.
- **`/api/tempo/avancar` estava aberto e mexia em dinheiro**: cada chamada soma kWh e reais em toda sessão ativa (é a conta que o motorista paga no fim). Sem login, dava pra inflar a fatura de todo mundo em looping. Passou a exigir admin — nenhuma tela usa essa rota, o próprio servidor avança o tempo sozinho.
- **Motorista via o histórico de pagamento de outro**: o histórico era casado pela placa mascarada (`ABC**23`), e duas placas com as mesmas 3 primeiras e 2 últimas posições geram a mesma máscara. Reproduzido na prática: `ABC9Z23`, recém-cadastrada, enxergava as 9 sessões de `ABC1D23`. O PIN não protegia nada aqui — o invasor usa o PIN da própria conta. Agora cada sessão guarda `conta_id` (vínculo exato), e as sessões antigas são adotadas pela conta certa numa migração automática no boot.
- **Faturamento acumulado numa rota sem login**: `/api/painel` (aberta, porque o totem depende dela) devolvia `receita_total` e o consumo total do dia. Foram pro `/api/kpis`, que já exige admin; o dashboard passou a ler de lá.
- **A chave do chatbot derrubava o sistema inteiro**: sem `GROQ_API_KEY`, o `import` do chatbot estourava `KeyError` e a API não subia — totem, dashboard, sessões e pagamento caíam junto por causa do chat. O cliente do Groq agora só é criado na primeira pergunta; sem a chave, só o `/api/chat` falha, com mensagem dizendo o que fazer.
- **Cadastro pelo menu do console quebrava**: a opção 6 chamava `cadastrar_usuario(placa, nome)` sem o PIN, que virou obrigatório — `TypeError` na cara de quem usasse. Passou a pedir o PIN.
- **A busca do chatbot era praticamente aleatória**: ela casava qualquer palavra da pergunta dentro do documento, incluindo "o", "de", "e" — então "o que é DLB?" e "quanto dura a bateria?" recebiam os mesmos 5 documentos de receita por carregador. Agora ignora palavra vazia e acento, compara palavra inteira (não pedaço: "dura" casava com "duração") e ordena por quantos termos casaram; se nada casa, manda contexto nenhum em vez de contexto errado.
- **Rótulo invertido no "+ Adicionar carro"**: dizia que a outra placa "já precisa estar cadastrada", quando a API exige exatamente o contrário — quem seguisse a instrução falhava sempre.
- **Histórico do app parava calado**: se a resposta viesse com erro (o limite de 20 consultas/minuto, por exemplo), a tela caía em `TypeError` e simplesmente parava de atualizar, sem avisar nada.
- **Link do badge do Colab apontava pra um notebook que não existe** no repositório (`..._Sprint2.ipynb`) — dava 404 em quem clicasse.

E o desempenho, que era o problema mais visível numa demonstração ao vivo:

- **`/api/painel` levava ~5,5s** — e o totem e o dashboard consultam essa rota a cada 3-4 segundos, ou seja, uma consulta ainda estava no ar quando a próxima começava, e a tela vivia atrasada. Três causas, todas medidas: (1) cada função de leitura abria uma conexão nova no Supabase, e abrir conexão custa ~1,3s; (2) o painel consultava as sessões ativas duas vezes por requisição; (3) `localhost` no Windows resolve pra IPv6 primeiro, o Flask escuta em IPv4, e cada chamada perdia ~1,8s no endereço errado. Com pool de conexões, consulta única e `127.0.0.1` nos front-ends: **~0,3s, cerca de 18x mais rápido**.
- Conexão vazada em qualquer erro: as funções fechavam a conexão na última linha, então uma exceção no meio deixava a conexão pendurada até estourar o limite do Supabase. O `conectar()` agora devolve sempre, e descarta a conexão que deu erro em vez de reaproveitar uma quebrada.

<br>

## Novidades (comparação com o projeto de um colega no mesmo desafio)

Depois de revisar o repositório de um projeto parecido de outro grupo no mesmo desafio (desktop local, sem nuvem, chatbot de palavra-chave — bem mais simples que o nosso em quase todo eixo técnico), três ideias de produto valiam a pena, reimplementadas do zero no nosso stack:

- **Manutenção de estação** — terceiro estado além de Livre/Ocupada. `manutencao_estacoes` (Postgres, não em memória — um carregador quebrado continua quebrado depois da API reiniciar) guarda quais estações estão fora de circulação e por quê. O admin marca/desmarca pelo dashboard (`POST /api/estacoes/<n>/manutencao` e `.../manutencao/encerrar`, os dois exigindo login); o motor recusa marcar manutenção em cima de uma sessão ativa (`entrar_em_manutencao` retorna `False`) e nunca deixa a manutenção interromper quem já está carregando (`aplicar_manutencao` nunca sobrescreve "Ocupada"). O totem detecta o estado pelo `/api/painel` e bloqueia o fluxo de recarga inteiro antes mesmo do motorista digitar a placa — não só recusa no fim.
- **Tarifa de madrugada com desconto** (`ia_calcular_tarifa`, 0h–6h, até 20% mais barato) — antes a tarifa dinâmica só subia no pico; agora também desce fora dele, o que é o argumento real de "tarifa dinâmica numa rede elétrica": não é só faturar mais no horário caro, é incentivar o motorista a mudar de horário e achatar a curva de demanda. Aparece pro motorista no totem (frase abaixo do botão "Iniciar recarga") e no dashboard (readout "Tarifa agora").
- **Relatório do dia pra download** — `GET /api/relatorio` (admin-only, como o `/api/kpis`) monta um `.txt` com faturamento, sessões, ticket médio e consumo do dia, devolvido com `Content-Disposition: attachment` — o botão "Baixar relatório do dia" no dashboard busca via `fetch` (pra mandar o token) e baixa como arquivo.

A quarta ideia — comissão/modelo de negócio documentado — virou [`docs/BUSINESS_MODEL.md`](BUSINESS_MODEL.md), escrito do zero refletindo a arquitetura real daqui (nuvem, LLM real, PIN, deploy ao vivo), não uma tradução do outro projeto.

<br>

## Preparação pra apresentação: solar, OCPP e telemetria de hardware

A partir de uma análise competitiva (comparando o ChargeGrid com plataformas reais como Driivz e AMPECO), três recursos entraram — todos verificados contra API real antes de documentar, já que a análise que motivou isso tinha erros factuais sobre o próprio repositório (ver `docs/GOODWE_ROADMAP.md` pro detalhe da verificação). Ficaram descritos com detalhe técnico em `docs/ARCHITECTURE.md` (seção "Solar, OCPP e telemetria de hardware"):

- Janela de desconto solar (`entregas/solar_optimizer.py`), calculada a partir de previsão real de radiação solar (Open-Meteo).
- DLB comunicando o limite de potência de cada estação no vocabulário real do OCPP 1.6J (`SetChargingProfile`).
- Contrato de telemetria (`POST /api/estacoes/<n>/telemetria`) pronto pro sensor físico de ocupação que o hardware vai usar.

Também foi corrigido o roteiro do vídeo de apresentação ([`docs/ROTEIRO_PITCH.md`](ROTEIRO_PITCH.md)) pra não overclaimar coisa que o sistema não faz (gateway de pagamento é simulado, não "processado" sem qualificar) nem underclaimar o que já faz (autenticação é placa **+ PIN**, não só placa) — e a divisão de tarefas da reta final está em [`docs/TAREFAS_EQUIPE.md`](TAREFAS_EQUIPE.md).
