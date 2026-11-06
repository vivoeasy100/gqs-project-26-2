"""Repositório de Cursos em memória."""

from threading import Lock
from domain.curso import Curso
from domain.inscricao import Inscricao


class CursoRepository:
    """Armazenamento em memória de cursos com identificador inteiro auto-incremental."""

    def __init__(self) -> None:
        self._cursos: dict[int, Curso] = {}
        self._next_id = 1
        self._lock = Lock()

    def salvar(self, curso: Curso) -> int:
        """Salva um novo curso e retorna seu ID gerado."""
        with self._lock:
            curso_id = self._next_id
            self._next_id += 1
            self._cursos[curso_id] = curso
            return curso_id

    def atualizar(self, curso_id: int, curso: Curso) -> bool:
        """Atualiza a referência do curso existente."""
        with self._lock:
            if curso_id in self._cursos:
                self._cursos[curso_id] = curso
                return True
            return False

    def buscar_por_id(self, curso_id: int) -> Curso | None:
        """Busca curso pelo seu ID."""
        with self._lock:
            return self._cursos.get(curso_id)

    def listar(self) -> list[tuple[int, Curso]]:
        """Retorna todos os cursos como pares (id, curso)."""
        with self._lock:
            return list(self._cursos.items())

    def buscar_inscricoes_por_aluno(self, aluno_email: str) -> list[tuple[int, Curso, Inscricao]]:
        """Retorna todos os cursos e inscrições vinculados a um aluno."""
        resultado: list[tuple[int, Curso, Inscricao]] = []
        normalizado = aluno_email.lower().strip()
        with self._lock:
            for curso_id, curso in self._cursos.items():
                for insc in curso.inscricoes:
                    if insc.aluno.email.lower().strip() == normalizado:
                        resultado.append((curso_id, curso, insc))
        return resultado

    def limpar(self) -> None:
        """Limpa todos os cursos cadastrados."""
        with self._lock:
            self._cursos.clear()
            self._next_id = 1

