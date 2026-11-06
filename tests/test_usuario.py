"""Testes para Usuario (Entidade).

Rastreabilidade: US-04 c3, US-05 c1
"""

import pytest

from domain.usuario import Usuario
from domain.enums import Perfil
from domain.exceptions import UsuarioInvalido


class TestUsuario:
    """Testes da entidade Usuario."""

    # US-04 c3: E-mail em formato válido
    def test_us04_c3_usuario_email_valido_simples(self):
        """US-04 c3: E-mail simples válido é aceito."""
        usuario = Usuario(nome="João", email="joao@email.com", senha_hash="hash123", perfil=Perfil.ALUNO)
        assert usuario.email == "joao@email.com"

    def test_us04_c3_usuario_email_valido_com_subdominio(self):
        """US-04 c3: E-mail com subdomínio é aceito."""
        usuario = Usuario(nome="João", email="joao@empresa.com.br", senha_hash="hash123", perfil=Perfil.ALUNO)
        assert usuario.email == "joao@empresa.com.br"

    def test_us04_c3_usuario_email_invalido_sem_arroba(self):
        """US-04 c3: E-mail sem @ lança UsuarioInvalido."""
        with pytest.raises(UsuarioInvalido) as exc:
            Usuario(nome="João", email="joaoemail.com", senha_hash="hash123", perfil=Perfil.ALUNO)
        assert "inválido" in str(exc.value).lower()

    def test_us04_c3_usuario_email_invalido_sem_dominio(self):
        """US-04 c3: E-mail sem domínio válido lança UsuarioInvalido."""
        with pytest.raises(UsuarioInvalido) as exc:
            Usuario(nome="João", email="joao@", senha_hash="hash123", perfil=Perfil.ALUNO)
        assert "inválido" in str(exc.value).lower()

    def test_us04_c3_usuario_email_invalido_sem_ponto_no_dominio(self):
        """US-04 c3: E-mail sem ponto no domínio lança UsuarioInvalido."""
        with pytest.raises(UsuarioInvalido) as exc:
            Usuario(nome="João", email="joao@email", senha_hash="hash123", perfil=Perfil.ALUNO)
        assert "inválido" in str(exc.value).lower()

    # US-05 c1: Saber se é aluno ou coordenador
    def test_us05_c1_eh_coordenador_retorna_true_para_coordenador(self):
        """US-05 c1: eh_coordenador() retorna True para perfil COORDENADOR."""
        usuario = Usuario(nome="Maria", email="maria@email.com", senha_hash="hash123", perfil=Perfil.COORDENADOR)
        assert usuario.eh_coordenador() is True

    def test_us05_c1_eh_coordenador_retorna_false_para_aluno(self):
        """US-05 c1: eh_coordenador() retorna False para perfil ALUNO."""
        usuario = Usuario(nome="João", email="joao@email.com", senha_hash="hash123", perfil=Perfil.ALUNO)
        assert usuario.eh_coordenador() is False