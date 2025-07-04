from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils
from app.api.v1.endpoints import organizations, studies
from app.api.v1.endpoints import users as users_v1
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)

# Clinical dashboard endpoints
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(studies.router, prefix="/studies", tags=["studies"])
api_router.include_router(users_v1.router, prefix="/v1/users", tags=["users-clinical"])

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
