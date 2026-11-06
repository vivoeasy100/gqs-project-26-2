"""Testes para Periodo (Value Object).

Rastreabilidade: US-01 c3, US-03 c2, US-07 c4
"""

from datetime import date

import pytest

from domain.periodo import Periodo
from domain.exceptions import PeriodoInvalido


class TestPeriodo:
    """Testes do Value Object Periodo."""

    # US-01 c3: Data final não pode ser anterior à inicial
    def test_us01_c3_periodo_invalido_fim_antes_inicio(self):
        """US-01 c3: Data final anterior à inicial deve lançar PeriodoInvalido."""
        with pytest.raises(PeriodoInvalido) as exc:
            Periodo(inicio=date(2025, 6, 10), fim=date(2025, 6, 1))
        assert "não pode ser anterior" in str(exc.value)

    def test_us01_c3_periodo_valido_mesmo_dia(self):
        """US-01 c3: Período com mesmo dia de início e fim é válido."""
        periodo = Periodo(inicio=date(2025, 6, 1), fim=date(2025, 6, 1))
        assert periodo.inicio == date(2025, 6, 1)
        assert periodo.fim == date(2025, 6, 1)

    def test_us01_c3_periodo_valido_dias_diferentes(self):
        """US-01 c3: Período com dias diferentes é válido."""
        periodo = Periodo(inicio=date(2025, 6, 1), fim=date(2025, 6, 10))
        assert periodo.inicio == date(2025, 6, 1)
        assert periodo.fim == date(2025, 6, 10)

    # US-03 c2 · US-07 c4: Saber se uma data cai dentro do período (contem)
    def test_us03_c2_us07_c4_contem_data_dentro(self):
        """US-03 c2 · US-07 c4: Data dentro do período retorna True."""
        periodo = Periodo(inicio=date(2025, 6, 1), fim=date(2025, 6, 10))
        assert periodo.contem(date(2025, 6, 1)) is True  # início
        assert periodo.contem(date(2025, 6, 5)) is True  # meio
        assert periodo.contem(date(2025, 6, 10)) is True  # fim

    def test_us03_c2_us07_c4_contem_data_fora(self):
        """US-03 c2 · US-07 c4: Data fora do período retorna False."""
        periodo = Periodo(inicio=date(2025, 6, 1), fim=date(2025, 6, 10))
        assert periodo.contem(date(2025, 5, 31)) is False  # antes
        assert periodo.contem(date(2025, 6, 11)) is False  # depois