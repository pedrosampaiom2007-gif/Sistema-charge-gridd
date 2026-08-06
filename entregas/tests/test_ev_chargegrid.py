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
    rodam, então mocká-la é o que torna esse teste determinístico."""

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
        with patch("ev_chargegrid.psycopg2.connect") as mock_connect:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.side_effect = [(i,) for i in range(1, 1000)]
            mock_connect.return_value.cursor.return_value = mock_cursor
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


if __name__ == "__main__":
    unittest.main()
