"""Value Object: Periodo (Passo 2 e 3).

Regras:
- US-01 c3: Data final não pode ser anterior à inicial
- US-03 c2 · US-07 c4: Saber se uma data cai dentro do período (contem)
"""

from dataclasses import dataclass
from datetime import date

from .exceptions import PeriodoInvalido


@dataclass(frozen=True, slots=True)
class Periodo:
    """Período com início e fim (inclusivos)."""

    inicio: date
    fim: date

    def __post_init__(self) -> None:
        if self.fim < self.inicio:
            raise PeriodoInvalido(
                f"Data final ({self.fim}) não pode ser anterior à inicial ({self.inicio})"
            )

    def contem(self, dia: date) -> bool:
        """US-03 c2 · US-07 c4: Verifica se uma data está dentro do período (inclusivo)."""
        return self.inicio <= dia <= self.fim

    def __str__(self) -> str:
        return f"{self.inicio} a {self.fim}"