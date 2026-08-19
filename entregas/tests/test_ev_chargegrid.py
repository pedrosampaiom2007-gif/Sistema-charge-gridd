"""
Testes automatizados do motor (ev_chargegrid.py).

Cobre só o que dá pra testar sem tocar no Postgres de verdade (compartilhado
com API/dashboard/chatbot, não é um banco de teste descartável):
  - lógica pura (hash de placa, mascaramento LGPD, tarifação dinâmica, DLB)
  - regressão da demonstracao_comercial() com o banco mockado (psycopg2)

Como rodar (da raiz do repo):
    python -m unittest discover -s entregas/tests -v
"""

import contextlib
import io
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ev_chargegrid as cg


class TestHashingEMascaramento(unittest.TestCase):

    def test_hash_placa_e_deterministico(self):
        self.assertEqual(cg.gerar_hash_placa("ABC1D23"), cg.gerar_hash_placa("ABC1D23"))

    def test_hash_placa_ignora_caixa_e_espacos(self):
        self.assertEqual(cg.gerar_hash_placa("abc1d23"), cg.gerar_hash_placa(" ABC1D23 "))

    def test_hash_placa_diferencia_placas_diferentes(self):
        self.assertNotEqual(cg.gerar_hash_placa("ABC1D23"), cg.gerar_hash_placa("XYZ9F88"))

    def test_mascarar_id_formato_lgpd(self):
        self.assertEqual(cg.mascarar_id("ABC1D23"), "ABC**23")

    def test_mascarar_id_string_curta(self):
        self.assertEqual(cg.mascarar_id("AB"), "AB**")

    def test_hash_senha_e_deterministico(self):
        self.assertEqual(cg.gerar_hash_senha("chargegrid2026"), cg.gerar_hash_senha("chargegrid2026"))

    def test_hash_senha_diferencia_senhas_diferentes(self):
        self.assertNotEqual(cg.gerar_hash_senha("senha1"), cg.gerar_hash_senha("senha2"))


class TestTarifacaoDinamica(unittest.TestCase):
    """ia_calcular_tarifa isolada de ia_prever_demanda: a demanda real depende
    de modelo_demanda.pkl estar carregado ou não no ambiente onde os testes
    rodam, então mocká-la é o que torna esse teste determinístico.

    Isolada também de solar_optimizer: sem o setUp/tearDown abaixo, boa parte
    destes testes bateria de verdade na Open-Meteo (rede real) e o resultado
    mudaria dependendo do clima/hora em que os testes rodassem — os testes
    do desconto solar em si ficam em TestDescontoSolar, com o mock explícito."""

    def setUp(self):
        self._patch_solar = patch.object(cg.solar_optimizer, "esta_em_janela_solar", return_value=False)
        self._patch_solar.start()

    def tearDown(self):
        self._patch_solar.stop()

    def test_fator_base_fora_de_pico_demanda_baixa(self):
        with patch.object(cg, "ia_prever_demanda", return_value=0.5):
            self.assertEqual(cg.ia_calcular_tarifa(hora=10, estacoes_ativas=1), 1.0)

    def test_horario_de_almoco_adiciona_30_por_cento(self):
        with patch.object(cg, "ia_prever_demanda", return_value=0.5):
            self.assertEqual(cg.ia_calcular_tarifa(hora=12, estacoes_ativas=1), 1.30)

    def test_horario_pico_noturno_adiciona_30_por_cento(self):
        with patch.object(cg, "ia_prever_demanda", return_value=0.5):
            for hora in (18, 19, 20):
                self.assertEqual(cg.ia_calcular_tarifa(hora=hora, estacoes_ativas=1), 1.30)

    def test_tres_ou_mais_estacoes_ativas_adiciona_15_por_cento(self):
        with patch.object(cg, "ia_prever_demanda", return_value=0.5):
            self.assertEqual(cg.ia_calcular_tarifa(hora=10, estacoes_ativas=3), 1.15)

    def test_demanda_alta_adiciona_20_por_cento(self):
        with patch.object(cg, "ia_prever_demanda", return_value=0.95):
            self.assertEqual(cg.ia_calcular_tarifa(hora=10, estacoes_ativas=1), 1.20)

    def test_demanda_media_adiciona_10_por_cento(self):
        with patch.object(cg, "ia_prever_demanda", return_value=0.80):
            self.assertEqual(cg.ia_calcular_tarifa(hora=10, estacoes_ativas=1), 1.10)

    def test_fatores_se_acumulam(self):
        # pico noturno (+0.30) + 3 estações ativas (+0.15) + demanda alta (+0.20)
        with patch.object(cg, "ia_prever_demanda", return_value=0.95):
            self.assertEqual(cg.ia_calcular_tarifa(hora=19, estacoes_ativas=3), 1.65)

    def test_madrugada_aplica_desconto(self):
        with patch.object(cg, "ia_prever_demanda", return_value=0.05):
            for hora in range(cg.HORA_INICIO_MADRUGADA, cg.HORA_FIM_MADRUGADA):
                self.assertEqual(cg.ia_calcular_tarifa(hora=hora, estacoes_ativas=1), 0.80)

    def test_madrugada_nao_afeta_horario_normal(self):
        with patch.object(cg, "ia_prever_demanda", return_value=0.5):
            self.assertEqual(cg.ia_calcular_tarifa(hora=cg.HORA_FIM_MADRUGADA, estacoes_ativas=1), 1.0)

    def test_desconto_de_madrugada_nunca_passa_do_piso(self):
        # mesmo se demanda alta empurrasse o fator pra cima, o desconto não
        # pode deixar a tarifa abaixo de 0.80 — max() garante o piso.
        with patch.object(cg, "ia_prever_demanda", return_value=0.99):
            fator = cg.ia_calcular_tarifa(hora=3, estacoes_ativas=1)
            self.assertGreaterEqual(fator, 0.80)


class TestDescontoSolar(unittest.TestCase):
    """O desconto solar depende de solar_optimizer.esta_em_janela_solar, que
    é mockado diretamente aqui — não testa a busca de dados em si (isso é
    TestSolarOptimizer), só a regra de como o resultado dela afeta o preço."""

    def test_aplica_desconto_dentro_da_janela_solar(self):
        with patch.object(cg, "ia_prever_demanda", return_value=0.5), \
             patch.object(cg.solar_optimizer, "esta_em_janela_solar", return_value=True):
            self.assertEqual(cg.ia_calcular_tarifa(hora=10, estacoes_ativas=1), 0.90)

    def test_nao_aplica_desconto_fora_da_janela_solar(self):
        with patch.object(cg, "ia_prever_demanda", return_value=0.5), \
             patch.object(cg.solar_optimizer, "esta_em_janela_solar", return_value=False):
            self.assertEqual(cg.ia_calcular_tarifa(hora=10, estacoes_ativas=1), 1.0)

    def test_pico_tem_prioridade_sobre_janela_solar(self):
        # hora 12 é pico de almoço — mesmo que o mock diga que é janela
        # solar, não faria sentido dar desconto justo na hora de maior
        # demanda, então o pico vence.
        with patch.object(cg, "ia_prever_demanda", return_value=0.5), \
             patch.object(cg.solar_optimizer, "esta_em_janela_solar", return_value=True):
            self.assertEqual(cg.ia_calcular_tarifa(hora=12, estacoes_ativas=1), 1.30)

    def test_madrugada_tem_prioridade_sobre_janela_solar(self):
        # cenário artificial (geração solar real é zero de madrugada), só
        # pra garantir que a estrutura if/elif nunca aplica os dois juntos.
        with patch.object(cg, "ia_prever_demanda", return_value=0.05), \
             patch.object(cg.solar_optimizer, "esta_em_janela_solar", return_value=True):
            self.assertEqual(cg.ia_calcular_tarifa(hora=3, estacoes_ativas=1), 0.80)

    def test_desconto_solar_nunca_passa_do_piso(self):
        with patch.object(cg, "ia_prever_demanda", return_value=0.99), \
             patch.object(cg.solar_optimizer, "esta_em_janela_solar", return_value=True):
            fator = cg.ia_calcular_tarifa(hora=10, estacoes_ativas=3)
            self.assertGreaterEqual(fator, 0.85)


class TestSolarOptimizer(unittest.TestCase):
    """Testa solar_optimizer isoladamente, sem bater na Open-Meteo de
    verdade — a busca real (_buscar_curva_open_meteo) é mockada em cada
    teste; só o comportamento de cache, fallback e seleção da janela é
    testado aqui."""

    def setUp(self):
        import solar_optimizer
        self.solar = solar_optimizer
        # cada teste começa com o cache vazio, senão um teste que rodou antes
        # (ou uma chamada real durante outro teste do arquivo) vazaria estado
        self.solar._cache_data = None
        self.solar._cache_curva = None
        self.solar._cache_fonte = None
        self.solar._proxima_tentativa = 0.0

    def tearDown(self):
        self.solar._cache_data = None
        self.solar._cache_curva = None
        self.solar._cache_fonte = None
        self.solar._proxima_tentativa = 0.0

    def test_cai_no_fallback_se_a_api_falhar(self):
        with patch.object(self.solar, "_buscar_curva_open_meteo", side_effect=TimeoutError):
            curva = self.solar.curva_solar_hoje()
        self.assertEqual(curva, self.solar._CURVA_FALLBACK)
        self.assertEqual(self.solar.fonte_da_previsao(), "fallback")

    def test_usa_a_curva_real_quando_a_api_responde(self):
        curva_falsa = {h: 0.0 for h in range(24)}
        curva_falsa[14] = 1.0
        with patch.object(self.solar, "_buscar_curva_open_meteo", return_value=curva_falsa):
            curva = self.solar.curva_solar_hoje()
        self.assertEqual(curva, curva_falsa)
        self.assertEqual(self.solar.fonte_da_previsao(), "open-meteo")

    def test_so_busca_uma_vez_por_dia_mesmo_com_varias_chamadas(self):
        with patch.object(self.solar, "_buscar_curva_open_meteo", return_value=dict(self.solar._CURVA_FALLBACK)) as mock_busca:
            self.solar.curva_solar_hoje()
            self.solar.curva_solar_hoje()
            self.solar.janela_solar_hoje()
        self.assertEqual(mock_busca.call_count, 1)

    def test_fallback_nao_trava_o_dia_todo_tenta_de_novo_apos_o_intervalo(self):
        """Regressão: antes, uma falha (ex: timeout no cold start de um
        deploy hibernado) prendia o sistema no perfil sintético até virar a
        data, mesmo que a rede voltasse a funcionar minutos depois — porque
        o cache só olhava a data, não se a última tentativa deu certo."""
        with patch.object(self.solar, "_buscar_curva_open_meteo", side_effect=TimeoutError) as mock_busca:
            self.solar.curva_solar_hoje()
            self.solar.curva_solar_hoje()  # ainda dentro do intervalo — não tenta de novo
        self.assertEqual(mock_busca.call_count, 1)

        # simula o intervalo de retentativa já ter passado
        self.solar._proxima_tentativa = 0.0
        with patch.object(self.solar, "_buscar_curva_open_meteo", return_value={h: 0.5 for h in range(24)}) as mock_busca:
            curva = self.solar.curva_solar_hoje()
        self.assertEqual(mock_busca.call_count, 1)
        self.assertEqual(self.solar.fonte_da_previsao(), "open-meteo")
        self.assertEqual(curva[0], 0.5)

    def test_sucesso_nao_reconsulta_pelo_resto_do_dia(self):
        """Diferente do fallback: um sucesso vale o dia inteiro — a previsão
        de manhã cedo não muda o suficiente hora a hora pra justificar bater
        na API de novo antes de virar a data."""
        with patch.object(self.solar, "_buscar_curva_open_meteo", return_value=dict(self.solar._CURVA_FALLBACK)) as mock_busca:
            self.solar.curva_solar_hoje()
        # mesmo "avançando" o relógio de retentativa manualmente, sucesso
        # não deveria nem olhar pra _proxima_tentativa
        self.solar._proxima_tentativa = 0.0
        with patch.object(self.solar, "_buscar_curva_open_meteo", return_value=dict(self.solar._CURVA_FALLBACK)) as mock_busca_2:
            self.solar.curva_solar_hoje()
        self.assertEqual(mock_busca_2.call_count, 0)

    def test_janela_solar_pega_as_horas_de_maior_geracao(self):
        curva_falsa = {h: 0.0 for h in range(24)}
        curva_falsa[11] = curva_falsa[12] = curva_falsa[13] = curva_falsa[14] = 1.0
        with patch.object(self.solar, "curva_solar_hoje", return_value=curva_falsa):
            janela = self.solar.janela_solar_hoje()
        self.assertEqual(janela, {11, 12, 13, 14})
        self.assertEqual(len(janela), self.solar.TAMANHO_JANELA_SOLAR)

    def test_esta_em_janela_solar_bate_com_janela_solar_hoje(self):
        with patch.object(self.solar, "janela_solar_hoje", return_value={9, 10, 11, 12}):
            self.assertTrue(self.solar.esta_em_janela_solar(10))
            self.assertFalse(self.solar.esta_em_janela_solar(20))

    def test_curva_para_api_tem_24_horas_marcando_a_janela(self):
        curva_falsa = {h: 0.0 for h in range(24)}
        curva_falsa[12] = 1.0
        with patch.object(self.solar, "curva_solar_hoje", return_value=curva_falsa), \
             patch.object(self.solar, "janela_solar_hoje", return_value={12}):
            saida = self.solar.curva_solar_para_api()
        self.assertEqual(len(saida), 24)
        hora_12 = next(x for x in saida if x["hora"] == 12)
        self.assertTrue(hora_12["janela_solar"])
        self.assertEqual(hora_12["geracao_relativa"], 1.0)
        hora_0 = next(x for x in saida if x["hora"] == 0)
        self.assertFalse(hora_0["janela_solar"])


class TestPrevisaoDemanda(unittest.TestCase):
    """Não trava no valor exato (depende do .pkl estar carregado ou cair no
    fallback), só garante o invariante que o resto do sistema depende dele
    respeitar: sempre entre 0.0 e 1.0."""

    def test_demanda_sempre_entre_0_e_1(self):
        for hora in range(24):
            demanda = cg.ia_prever_demanda(hora)
            self.assertGreaterEqual(demanda, 0.0)
            self.assertLessEqual(demanda, 1.0)


class TestBalanceamentoDeCarga(unittest.TestCase):
    """DLB — mexe direto no estado global cg.estacoes, por isso reseta antes
    e depois de cada teste pra não vazar estado entre eles."""

    def setUp(self):
        for e in cg.estacoes:
            e.encerrar()

    tearDown = setUp

    def test_sem_estacoes_ativas_nao_faz_nada(self):
        cg.balancear_carga()
        self.assertTrue(all(e.potencia_kw == 0.0 for e in cg.estacoes))

    def test_uma_estacao_ativa_recebe_potencia_maxima_por_estacao(self):
        cg.estacoes[0].ativa = True
        cg.balancear_carga()
        self.assertEqual(cg.estacoes[0].potencia_kw, cg.MAX_POTENCIA_ESTACAO)

    def test_divide_igualmente_entre_as_ativas(self):
        for e in cg.estacoes[:4]:
            e.ativa = True
        cg.balancear_carga()
        esperado = cg.LIMITE_POTENCIA_GRID / 4
        for e in cg.estacoes[:4]:
            self.assertAlmostEqual(e.potencia_kw, esperado)

    def test_respeita_teto_por_estacao_mesmo_com_poucas_ativas(self):
        # 50kW do grid / 2 estações = 25kW cada, mas o teto por estação é 22kW
        cg.estacoes[0].ativa = True
        cg.estacoes[1].ativa = True
        cg.balancear_carga()
        self.assertEqual(cg.estacoes[0].potencia_kw, cg.MAX_POTENCIA_ESTACAO)

    def test_estacoes_livres_nao_recebem_potencia(self):
        cg.estacoes[0].ativa = True
        cg.estacoes[1].ativa = False
        cg.balancear_carga()
        self.assertEqual(cg.estacoes[1].potencia_kw, 0.0)


class TestDemonstracaoFechaTodasAsSessoes(unittest.TestCase):
    """Regressão do bug corrigido nesta sessão: demonstracao_comercial()
    abria 4 sessões mas só chamava confirmar_pagamento() (que marca
    ativa=0 no Postgres) pra primeira. As outras 3 ficavam 'ativa=1' no
    banco pra sempre e voltavam como sessões fantasmas, ocupando estações
    reais, na próxima recuperação de sessões da API (_recuperar_sessoes_ativas
    em api_server.py). psycopg2.connect é mockado — não toca no Postgres
    real (compartilhado, não é um banco de teste)."""

    def setUp(self):
        for e in cg.estacoes:
            e.encerrar()

    tearDown = setUp

    def _rodar_demo_mockada(self):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [(i,) for i in range(1, 1000)]

        @contextlib.contextmanager
        def conexao_falsa(somente_leitura=False):
            conn = MagicMock()
            conn.cursor.return_value = mock_cursor
            yield conn

        # O mock passou a ser em cg.conectar (o pool de conexões) e não mais em
        # psycopg2.connect: o motor não abre conexão direta em lugar nenhum.
        with patch("ev_chargegrid.conectar", conexao_falsa):
            with contextlib.redirect_stdout(io.StringIO()):
                cg.demonstracao_comercial()
        return mock_cursor

    def test_todas_as_4_estacoes_ficam_inativas_apos_a_demo(self):
        self._rodar_demo_mockada()
        for i in range(4):
            self.assertFalse(cg.estacoes[i].ativa, f"estação {i + 1} continua ativa após a demo")

    def test_confirma_pagamento_das_4_sessoes_no_banco(self):
        mock_cursor = self._rodar_demo_mockada()
        updates_pagamento = [
            chamada for chamada in mock_cursor.execute.call_args_list
            if "UPDATE sessoes SET status_pagamento" in chamada.args[0]
        ]
        self.assertEqual(len(updates_pagamento), 4)


class TestAplicarManutencao(unittest.TestCase):
    """aplicar_manutencao é pura (recebe os dois dicts prontos, não toca no
    banco) de propósito — pra poder testar a regra de negócio (nunca
    sobrescrever Ocupada) sem precisar de conexão nenhuma."""

    def test_sobrescreve_livre_com_manutencao(self):
        status = {1: "Livre", 2: "Livre"}
        em_manutencao = {1: {"motivo": "cabo danificado"}}
        resultado = cg.aplicar_manutencao(status, em_manutencao)
        self.assertEqual(resultado[1], "Manutenção")
        self.assertEqual(resultado[2], "Livre")

    def test_nunca_sobrescreve_ocupada(self):
        # sessão em andamento não pode ser interrompida por uma manutenção
        # marcada durante ela (entrar_em_manutencao já recusa isso, mas essa
        # função é a segunda linha de defesa caso os dois fiquem inconsistentes)
        status = {1: "Ocupada"}
        em_manutencao = {1: {"motivo": None}}
        resultado = cg.aplicar_manutencao(status, em_manutencao)
        self.assertEqual(resultado[1], "Ocupada")

    def test_sem_manutencao_nenhuma_nao_muda_nada(self):
        status = {1: "Livre", 2: "Ocupada"}
        resultado = cg.aplicar_manutencao(status, {})
        self.assertEqual(resultado, status)


class TestRelatorioDoDia(unittest.TestCase):
    """relatorio_do_dia só agrupa números que já vêm de funções de leitura
    testadas isoladamente — aqui a gente garante que o agrupamento (ticket
    médio, principalmente) está certo, mockando as leituras."""

    def test_agrupa_os_numeros_certos(self):
        with patch.object(cg, "obter_faturamento_dia", return_value=245.80), \
             patch.object(cg, "contar_sessoes_dia", return_value=6), \
             patch.object(cg, "obter_consumo_dia", return_value=58.4), \
             patch.object(cg, "contar_ativas", return_value=2):
            r = cg.relatorio_do_dia("2026-08-08")
        self.assertEqual(r["data"], "2026-08-08")
        self.assertEqual(r["faturamento"], 245.80)
        self.assertEqual(r["sessoes_dia"], 6)
        self.assertAlmostEqual(r["ticket_medio"], 40.97, places=2)
        self.assertEqual(r["consumo_kwh"], 58.4)
        self.assertEqual(r["estacoes_ativas_agora"], 2)

    def test_ticket_medio_zero_sem_sessao_nao_divide_por_zero(self):
        with patch.object(cg, "obter_faturamento_dia", return_value=0.0), \
             patch.object(cg, "contar_sessoes_dia", return_value=0), \
             patch.object(cg, "obter_consumo_dia", return_value=0.0), \
             patch.object(cg, "contar_ativas", return_value=0):
            r = cg.relatorio_do_dia("2026-08-08")
        self.assertEqual(r["ticket_medio"], 0.0)


class TestStatusDasSessoes(unittest.TestCase):
    """status_das_sessoes deriva o mesmo resultado de obter_status_estacoes()
    a partir de uma lista já em mãos, sem ir ao banco — é o que tirou a
    consulta duplicada do /api/painel."""

    def test_marca_ocupada_so_o_que_tem_sessao(self):
        status = cg.status_das_sessoes([{"estacao": 2}, {"estacao": 7}])
        self.assertEqual(status[2], "Ocupada")
        self.assertEqual(status[7], "Ocupada")
        self.assertEqual(status[1], "Livre")

    def test_cobre_todas_as_estacoes(self):
        status = cg.status_das_sessoes([])
        self.assertEqual(len(status), cg.MAX_ESTACOES)
        self.assertTrue(all(v == "Livre" for v in status.values()))


class TestBuscaDoRag(unittest.TestCase):
    """Regressão da busca do RAG: ela casava qualquer palavra da pergunta,
    inclusive "o"/"de"/"e", então quase toda pergunta trazia os mesmos 5
    documentos de receita — inclusive perguntas sobre bateria de carro
    elétrico, que não têm nada a ver com o histórico comercial."""

    def setUp(self):
        # importado aqui (e não no topo) porque só este teste precisa do
        # chatbot; o resto do arquivo testa só o motor.
        import chatbot
        self.chatbot = chatbot

    def test_ignora_palavras_vazias(self):
        self.assertEqual(self.chatbot._palavras_uteis("o que e isso de a"), [])

    def test_pergunta_sem_relacao_nao_traz_documento(self):
        self.assertEqual(self.chatbot.buscar_documentos("quanto dura a bateria do meu carro"), [])

    def test_pergunta_sobre_o_negocio_traz_documento(self):
        docs = self.chatbot.buscar_documentos("qual o ticket medio historico")
        self.assertTrue(docs)
        self.assertTrue(all("ticket" in d.lower() for d in docs))

    def test_ignora_acento(self):
        com_acento = self.chatbot.buscar_documentos("qual a receita por sessões")
        sem_acento = self.chatbot.buscar_documentos("qual a receita por sessoes")
        self.assertEqual(com_acento, sem_acento)
        self.assertTrue(com_acento)

    def test_ordena_pelo_numero_de_termos_que_casam(self):
        docs = self.chatbot.buscar_documentos("dlb variancia consumo")
        self.assertTrue(docs)
        self.assertIn("DLB", docs[0])


class TestAcessoAoContextoDeNegocio(unittest.TestCase):
    """O contexto do chat é fail-closed: sem acesso_gestao explícito, nenhum
    número de negócio entra na resposta. Antes era o contrário — o acesso
    total era o padrão e a restrição era opt-in."""

    def setUp(self):
        import chatbot
        self.chatbot = chatbot

    def test_padrao_nao_inclui_historico_comercial(self):
        contexto = self.chatbot.buscar_contexto("qual o ticket medio historico")
        self.assertEqual(contexto, "")

    def test_gestao_inclui_historico_comercial(self):
        contexto = self.chatbot.buscar_contexto("qual o ticket medio historico", acesso_gestao=True)
        self.assertIn("DADOS HISTÓRICOS", contexto)

    def test_padrao_mostra_disponibilidade_mas_nao_faturamento(self):
        with patch.object(self.chatbot, "obter_status_estacoes", return_value={1: "Livre", 2: "Ocupada"}):
            contexto = self.chatbot.buscar_contexto("tem estação livre agora?")
        self.assertIn("DISPONIBILIDADE", contexto)
        self.assertNotIn("Faturamento", contexto)


if __name__ == "__main__":
    unittest.main()
