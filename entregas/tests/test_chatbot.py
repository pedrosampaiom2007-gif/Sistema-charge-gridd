"""
Testes automatizados do chatbot (chatbot.py) — só a lógica pura
(_sanitizar_formatacao). O resto (buscar_documentos, responder) depende do
Groq e/ou do Postgret real, testado manualmente contra a API ao vivo, mesmo
padrão do resto do projeto.

Como rodar (da raiz do repo):
    python -m unittest discover -s entregas/tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chatbot


class TestSanitizarFormatacao(unittest.TestCase):
    """Regressão: testado ao vivo contra o Groq, a mesma pergunta às vezes
    voltava com tabela markdown inteira e cabeçalhos (##/###), mesmo com
    instrução explícita no prompt pra não usar — o balão de chat é estreito
    demais pra tabela, e o renderizador de Markdown do front não trata
    tabela (apareceria "|" literal na tela). Essa função é a segunda camada
    de defesa (a primeira é a instrução no prompt + temperature mais baixa,
    que não são testáveis de forma determinística aqui)."""

    def test_texto_normal_passa_sem_alteracao(self):
        texto = "A bateria costuma durar de 8 a 12 anos.\nQuer saber mais?"
        self.assertEqual(chatbot._sanitizar_formatacao(texto), texto)

    def test_cabecalho_vira_negrito(self):
        self.assertEqual(
            chatbot._sanitizar_formatacao("### Como cuidar da bateria"),
            "**Como cuidar da bateria**",
        )

    def test_cabecalho_nivel_2_tambem_vira_negrito(self):
        self.assertEqual(
            chatbot._sanitizar_formatacao("## Autonomia"),
            "**Autonomia**",
        )

    def test_linha_separadora_de_tabela_e_removida(self):
        self.assertEqual(chatbot._sanitizar_formatacao("|---|---|"), "")

    def test_linha_de_tabela_vira_item_de_lista(self):
        self.assertEqual(
            chatbot._sanitizar_formatacao("| Fator | Efeito |"),
            "- **Fator**: Efeito",
        )

    def test_linha_de_tabela_com_mais_de_duas_colunas(self):
        self.assertEqual(
            chatbot._sanitizar_formatacao("| Tipo 1 | 32A | América do Norte |"),
            "- **Tipo 1**: 32A — América do Norte",
        )

    def test_tabela_completa_vira_lista_sem_linha_separadora(self):
        tabela = (
            "| Fator | Efeito |\n"
            "|-------|--------|\n"
            "| Temperatura | Reduz a vida útil |\n"
            "| Ciclos de carga | Desgasta a bateria |"
        )
        esperado = (
            "- **Fator**: Efeito\n"
            "- **Temperatura**: Reduz a vida útil\n"
            "- **Ciclos de carga**: Desgasta a bateria"
        )
        self.assertEqual(chatbot._sanitizar_formatacao(tabela), esperado)

    def test_texto_misto_com_cabecalho_tabela_e_paragrafo(self):
        texto = (
            "Resumo:\n"
            "### Comparação\n"
            "| A | B |\n"
            "|---|---|\n"
            "| 1 | 2 |\n"
            "Fim."
        )
        resultado = chatbot._sanitizar_formatacao(texto)
        self.assertNotIn("#", resultado)
        self.assertNotIn("|", resultado)
        self.assertIn("**Comparação**", resultado)
        self.assertIn("- **A**: B", resultado)
        self.assertIn("- **1**: 2", resultado)
        self.assertIn("Fim.", resultado)


if __name__ == "__main__":
    unittest.main()
