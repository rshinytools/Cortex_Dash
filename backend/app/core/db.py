from sqlmodel import Session, create_engine, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from app import crud
from app.core.config import settings
from app.models import User, UserCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))

# Create async engine for async endpoints
async_database_url = str(settings.SQLALCHEMY_DATABASE_URI).replace("postgresql://", "postgresql+asyncpg://")
async_engine: AsyncEngine = create_async_engine(async_database_url, echo=False)


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
            role="system_admin",  # Set the correct role for the first superuser
        )
        user = crud.create_user(session=session, user_create=user_in)
    elif user.role != "system_admin":
        # Update existing superuser to have the correct role
        user.role = "system_admin"
        session.add(user)
        session.commit()
