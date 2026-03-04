# Routers package
from app.routers.auth_router import router as auth_router
from app.routers.analysis_router import router as analysis_router
from app.routers.admin_router import router as admin_router
from app.routers.websocket_router import router as websocket_router
from app.routers.extension_router import router as extension_router

__all__ = [
    "auth_router",
    "analysis_router",
    "admin_router",
    "websocket_router",
    "extension_router",
]
