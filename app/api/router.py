from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.categorias import router as categorias_router
from app.api.routes.clientes import router as clientes_router
from app.api.routes.inventario import router as inventario_router
from app.api.routes.productos import router as productos_router
from app.api.routes.ventas import router as ventas_router
from app.database.session import SessionLocal


api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


@api_router.get("/health/db", tags=["Health"])
def database_health_check():
    if SessionLocal is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable",
        )

    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable",
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable",
        ) from error

    return {"status": "ok", "database": "connected"}


api_router.include_router(categorias_router)
api_router.include_router(clientes_router)
api_router.include_router(inventario_router)
api_router.include_router(productos_router)
api_router.include_router(ventas_router)
