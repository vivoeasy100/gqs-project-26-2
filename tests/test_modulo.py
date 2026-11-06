"""Testes para Modulo (Entidade).

Rastreabilidade: US-02 c4
"""

import pytest

from domain.modulo import Modulo
from domain.exceptions import ModuloInvalido
from datetime import date


class TestModulo:
    """Testes da entidade Modulo."""

    # US-02 c4: Link precisa ser uma URL
    def test_us02_c4_modulo_link_valido_http(self):
        """US-02 c4: Link HTTP válido é aceito."""
        modulo = Modulo(titulo="Módulo 1", link="http://example.com/video")
        assert modulo.link == "http://example.com/video"

    def test_us02_c4_modulo_link_valido_https(self):
        """US-02 c4: Link HTTPS válido é aceito."""
        modulo = Modulo(titulo="Módulo 1", link="https://www.youtube.com/watch?v=abc")
        assert modulo.link == "https://www.youtube.com/watch?v=abc"

    def test_us02_c4_modulo_link_valido_com_porta(self):
        """US-02 c4: Link com porta é aceito."""
        modulo = Modulo(titulo="Módulo 1", link="http://localhost:8080/meet")
        assert modulo.link == "http://localhost:8080/meet"

    def test_us02_c4_modulo_link_invalido_sem_scheme(self):
        """US-02 c4: Link sem scheme (http/https) lança ModuloInvalido."""
        with pytest.raises(ModuloInvalido) as exc:
            Modulo(titulo="Módulo 1", link="example.com/video")
        assert "inválido" in str(exc.value).lower()

    def test_us02_c4_modulo_link_invalido_sem_netloc(self):
        """US-02 c4: Link sem netloc lança ModuloInvalido."""
        with pytest.raises(ModuloInvalido) as exc:
            Modulo(titulo="Módulo 1", link="http:///video")
        assert "inválido" in str(exc.value).lower()

    def test_us02_c4_modulo_link_invalido_string_vazia(self):
        """US-02 c4: Link vazio lança ModuloInvalido."""
        with pytest.raises(ModuloInvalido):
            Modulo(titulo="Módulo 1", link="")

    def test_modulo_data_opcional(self):
        """Módulo pode ser criado sem data (para gravado)."""
        modulo = Modulo(titulo="Módulo 1", link="https://youtube.com/v1")
        assert modulo.data is None

    def test_modulo_com_data(self):
        """Módulo pode ser criado com data (para síncrono)."""
        modulo = Modulo(titulo="Módulo 1", link="https://meet.google.com/xyz", data=date(2025, 6, 15))
        assert modulo.data == date(2025, 6, 15)