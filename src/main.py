"""Ponto de entrada da aplicação FastAPI de Gestão de Cursos Online (v1)."""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes_auth import router as auth_router
from api.routes_cursos import router as cursos_router
from api.routes_inscricoes import router as inscricoes_router
from domain.exceptions import DominioError


def create_app() -> FastAPI:
    """Fábrica da aplicação FastAPI."""
    app = FastAPI(
        title="Sistema de Cursos Online - v1",
        description=(
            "API para gestão, publicação, inscrição e liberação de acesso a cursos online, "
            "implementada seguindo a abordagem bottom-up e testes de unidade e integração."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configuração de CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Tratamento global de erros de domínio não capturados nas rotas
    @app.exception_handler(DominioError)
    async def dominio_error_handler(request: Request, exc: DominioError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc), "tipo_erro": exc.__class__.__name__},
        )

    # Inclusão dos roteadores
    app.include_router(auth_router)
    app.include_router(cursos_router)
    app.include_router(inscricoes_router)

    @app.get("/", tags=["Saúde"])
    def root() -> dict[str, str]:
        return {
            "sistema": "Cursos Online v1",
            "status": "operacional",
            "docs": "/docs",
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

